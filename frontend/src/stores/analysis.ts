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
    return 'Agent 工作流正在逐步分析...'
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

  async function analyze() {
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
    report.value = null  // 清空上次结果
    startTimer()

    try {
      const result = await runJDMatch(
        {
          resume_text: resumeText.value,
          jd_text: jdText.value,
          company: jdCompany.value.trim(),
          position: jdPosition.value.trim(),
        },
        { signal: currentController.signal },
      )
      if (requestId !== activeRequestId) return
      report.value = result
      if (result.progress_log?.length) {
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
      }, { params: { match_score: report.value.match_score }, timeout: 60000 })
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
