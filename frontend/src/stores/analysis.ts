import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  type JDMatchResponse,
  getProgress,
  runJDMatch,
} from '@/api'

export const useAnalysisStore = defineStore('analysis', () => {
  const resumeText = ref('')
  const jdText = ref('')
  const jdCompany = ref('')
  const jdPosition = ref('')
  const report = ref<JDMatchResponse | null>(null)
  const loading = ref(false)
  const rewriteLoading = ref(false)
  const error = ref('')
  const elapsedSeconds = ref(0)
  const progressSteps = ref<string[]>([])
  const progressDone = ref(false)

  let timer: ReturnType<typeof setInterval> | null = null
  let progressPoller: ReturnType<typeof setInterval> | null = null
  let currentController: AbortController | null = null
  let activeRequestId = 0

  const statusMessage = computed(() => {
    if (!loading.value) return ''
    if (progressSteps.value.length) {
      return progressSteps.value[progressSteps.value.length - 1] || 'Agent 正在分析...'
    }
    return 'Agent 正在启动...'
  })

  function startTimer() {
    elapsedSeconds.value = 0
    progressSteps.value = []
    progressDone.value = false
    if (timer) window.clearInterval(timer)
    timer = window.setInterval(() => { elapsedSeconds.value += 1 }, 1000)
  }

  function stopTimer() {
    if (timer) { window.clearInterval(timer); timer = null }
    if (progressPoller) { window.clearInterval(progressPoller); progressPoller = null }
  }

  function getErrorMessage(e: unknown) {
    if (typeof e === 'object' && e !== null) {
      const err = e as { code?: string; message?: string; response?: { data?: { detail?: string } } }
      if (err.code === 'ERR_CANCELED') return ''
      if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
        return '分析超时，请稍后重试。如持续超时可检查网络或 API Key 配置。'
      }
      return err.response?.data?.detail || err.message || '分析失败'
    }
    return '分析失败'
  }

  async function analyze(confirmed = false) {
    if (!resumeText.value.trim() || !jdText.value.trim()) {
      error.value = '请同时填写简历内容和目标 JD'
      return
    }
    if (!jdCompany.value.trim() || !jdPosition.value.trim()) {
      error.value = '请填写公司名称和岗位名称，方便后续归档搜索'
      return
    }

    const requestId = activeRequestId + 1
    activeRequestId = requestId
    currentController = new AbortController()

    loading.value = true
    error.value = ''
    if (!confirmed) report.value = null
    startTimer()

    try {
      const result = await runJDMatch(
        {
          resume_text: resumeText.value,
          jd_text: jdText.value,
          company: jdCompany.value.trim(),
          position: jdPosition.value.trim(),
          confirmed,
        },
        { signal: currentController.signal },
      )
      if (requestId !== activeRequestId) return

      // Pre-check: show dialog to collect missing info
      if (result.degraded && result.pre_check?.length) {
        loading.value = false
        stopTimer()
        const warnings = result.pre_check.filter((c: any) => c.type !== 'ok')
        const hasEdu = warnings.some((c: any) => c.msg.includes('学历'))

        if (hasEdu) {
          // Show inline form to fill education
          const { ElMessageBox } = await import('element-plus')
          try {
            const { value } = await ElMessageBox.prompt(
              '请输入最高学历信息（例如：硕士 吉林大学 计算机）',
              '补充学历信息',
              { confirmButtonText: '补充后继续', cancelButtonText: '跳过', inputPlaceholder: '硕士 吉林大学 计算机科学与技术' }
            )
            if (value?.trim()) {
              resumeText.value = resumeText.value + '\n学历：' + value.trim()
            }
          } catch { /* skip */ }
          await analyze(true)
        } else {
          const { ElMessageBox } = await import('element-plus')
          const msg = warnings.map((c: any) => `${c.type === 'warning' ? '⚠️' : 'ℹ️'} ${c.msg}`).join('<br>')
          try {
            await ElMessageBox.confirm(
              `<div style="line-height:2">${msg}</div><br>是否继续分析？`,
              'Agent 预检查',
              { dangerouslyUseHTMLString: true, confirmButtonText: '继续分析', cancelButtonText: '补充信息', type: 'warning' }
            )
            await analyze(true)
          } catch { /* user chose to fix manually */ }
        }
        return
      }

      report.value = result
      // If session_id available, populate progress from it
      if (result.session_id) {
        try {
          const { getProgress } = await import('@/api')
          const pdata = await getProgress(result.session_id)
          if (pdata?.steps?.length) {
            progressSteps.value = pdata.steps
            progressDone.value = true
          }
        } catch { /* ignore poll errors */ }
      }
      // Show backend progress steps
      if (result.session_id) {
        try {
          const { getProgress } = await import('@/api')
          const pdata = await getProgress(result.session_id)
          if (pdata?.steps?.length) {
            progressSteps.value = pdata.steps
            progressDone.value = pdata.done
          }
        } catch { /* ignore */ }
      }
      if (!progressSteps.value.length && result.progress_log?.length) {
        progressSteps.value = result.progress_log
        progressDone.value = true
      }
    } catch (e: unknown) {
      if (requestId !== activeRequestId) return
      const msg = getErrorMessage(e)
      if (msg) error.value = msg
    } finally {
      if (requestId === activeRequestId) {
        loading.value = false
        currentController = null
        stopTimer()
      }
    }
  }

  function reset() {
    report.value = null
    error.value = ''
  }

  async function retestWithRevised() {
    if (!report.value?.revised_resume || !jdText.value.trim()) return
    resumeText.value = report.value.revised_resume
    await analyze()
  }

  async function rewriteResume() {
    if (rewriteLoading.value || !report.value || !jdText.value.trim() || !resumeText.value.trim()) return
    rewriteLoading.value = true
    error.value = ''
    try {
      const { default: client } = await import('@/api/client')
      const { data } = await client.post('/api/v1/analysis/rewrite-resume', {
        resume_text: resumeText.value,
        jd_text: jdText.value,
      }, { params: { match_score: report.value.match_score, report_id: report.value.id || 0 }, timeout: 60000 })
      if (data.revised_resume) {
        report.value = { ...report.value, revised_resume: data.revised_resume } as any
        // Trigger rewrite success dialog
        const { ElMessageBox } = await import('element-plus')
        const lines = data.revised_resume.split('\n').filter((l: string) => l.trim()).length
        ElMessageBox.alert(
          `<p>已生成 <b>${lines}</b> 行改写简历</p><p style='color:#22c55e'>仅优化表达，未编造经历</p><p style='color:#667085;font-size:13px'>请在下方面查看并手动调整，满意后可导出 Markdown 或 PDF。</p>`,
          '简历改写完成',
          { dangerouslyUseHTMLString: true, confirmButtonText: '查看', type: 'success' }
        ).catch(() => {})
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || '简历改写失败，请重试'
    } finally {
      rewriteLoading.value = false
    }
  }

  return {
    resumeText, jdText, jdCompany, jdPosition,
    report, loading, rewriteLoading, error,
    elapsedSeconds, progressSteps, progressDone,
    statusMessage,
    analyze, reset, retestWithRevised, rewriteResume,
  }
})
