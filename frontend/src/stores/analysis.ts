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

    const requestId = activeRequestId + 1
    activeRequestId = requestId
    currentController = new AbortController()

    loading.value = true
    error.value = ''
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

  return {
    resumeText, jdText, jdCompany, jdPosition,
    report, loading, error,
    elapsedSeconds, progressSteps, progressDone,
    statusMessage,
    analyze, reset, retestWithRevised,
  }
})
