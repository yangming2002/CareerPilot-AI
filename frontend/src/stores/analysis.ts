import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  type JDMatchResponse,
  getProgress,
  runJDMatch,
} from '@/api'

type AnalysisEngine = 'rule' | 'llm' | 'graph'

export const useAnalysisStore = defineStore('analysis', () => {
  const resumeText = ref('')
  const jdText = ref('')
  const report = ref<JDMatchResponse | null>(null)
  const loading = ref(false)
  const error = ref('')
  const engine = ref<AnalysisEngine>('rule')
  const elapsedSeconds = ref(0)
  const progressSteps = ref<string[]>([])
  const progressDone = ref(false)

  let timer: ReturnType<typeof setInterval> | null = null
  let progressPoller: ReturnType<typeof setInterval> | null = null
  let currentController: AbortController | null = null
  let activeRequestId = 0

  const isSlowLLM = computed(() => engine.value === 'llm' && loading.value && elapsedSeconds.value >= 10)
  const isVerySlowLLM = computed(() => engine.value === 'llm' && loading.value && elapsedSeconds.value >= 25)
  const statusMessage = computed(() => {
    if (!loading.value) return ''
    if (engine.value === 'rule') return '规则引擎正在快速分析，通常几秒内完成。'
    if (engine.value === 'graph' && progressSteps.value.length) {
      const last = progressSteps.value[progressSteps.value.length - 1]
      return last || 'Agent 工作流正在分析...'
    }
    if (engine.value === 'graph') return 'Agent 工作流正在逐步分析...'
    if (elapsedSeconds.value < 10) return 'LLM 正在深度分析 JD 和简历，请稍等。'
    if (elapsedSeconds.value < 25) return 'LLM 还在生成结构化报告，网络或模型繁忙时会变慢。'
    return 'LLM 已等待较久，可以继续等，也可以先切换到规则引擎拿到快速结果。'
  })

  function startTimer() {
    elapsedSeconds.value = 0
    progressSteps.value = []
    progressDone.value = false
    if (timer) window.clearInterval(timer)
    timer = window.setInterval(() => {
      elapsedSeconds.value += 1
    }, 1000)
  }

  function startProgressPolling(sessionId: string) {
    if (progressPoller) window.clearInterval(progressPoller)
    progressPoller = window.setInterval(async () => {
      try {
        const data = await getProgress(sessionId)
        progressSteps.value = data.steps
        progressDone.value = data.done
        if (data.done && progressPoller) {
          window.clearInterval(progressPoller)
          progressPoller = null
        }
      } catch {
        // Session not ready yet, keep polling
      }
    }, 500)
  }

  function stopProgressPolling() {
    if (progressPoller) {
      window.clearInterval(progressPoller)
      progressPoller = null
    }
  }

  function stopTimer() {
    if (timer) {
      window.clearInterval(timer)
      timer = null
    }
    stopProgressPolling()
  }

  function getErrorMessage(e: unknown, selectedEngine: AnalysisEngine) {
    if (typeof e === 'object' && e !== null) {
      const err = e as { code?: string; message?: string; response?: { data?: { detail?: string } } }
      if (err.code === 'ERR_CANCELED') return ''
      if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
        return selectedEngine === 'llm'
          ? 'LLM 分析超时。你可以先使用规则引擎获得快速匹配结果，稍后再重试 LLM。'
          : '规则分析请求超时，请检查后端服务是否正常。'
      }
      return err.response?.data?.detail || err.message || '分析失败'
    }
    return '分析失败'
  }

  async function analyze(forcedEngine?: AnalysisEngine) {
    if (loading.value && !forcedEngine) return
    if (!resumeText.value.trim() || !jdText.value.trim()) {
      error.value = '请同时填写简历内容和目标 JD'
      return
    }

    const selectedEngine = forcedEngine || engine.value
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
        },
        selectedEngine,
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
      const msg = getErrorMessage(e, selectedEngine)
      if (msg) error.value = msg
    } finally {
      if (requestId === activeRequestId) {
        loading.value = false
        currentController = null
        stopTimer()
      }
    }
  }

  async function cancelAndRunRule() {
    if (currentController) currentController.abort()
    activeRequestId += 1
    loading.value = false
    currentController = null
    stopTimer()
    engine.value = 'rule'
    await analyze('rule')
  }

  function reset() {
    report.value = null
    error.value = ''
  }

  async function retestWithRevised() {
    if (!report.value?.revised_resume || !jdText.value.trim()) return
    resumeText.value = report.value.revised_resume
    await analyze(engine.value)
  }

  return {
    resumeText,
    jdText,
    report,
    loading,
    error,
    engine,
    elapsedSeconds,
    progressSteps,
    progressDone,
    isSlowLLM,
    isVerySlowLLM,
    statusMessage,
    analyze,
    cancelAndRunRule,
    reset,
    retestWithRevised,
  }
})
