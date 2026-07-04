import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type JDMatchResponse,
  runJDMatch,
} from '@/api'

export const useAnalysisStore = defineStore('analysis', () => {
  const resumeText = ref('')
  const jdText = ref('')
  const report = ref<JDMatchResponse | null>(null)
  const loading = ref(false)
  const error = ref('')
  const engine = ref<'rule' | 'llm'>('rule')

  async function analyze() {
    if (!resumeText.value.trim() || !jdText.value.trim()) {
      error.value = '请同时填写简历内容和目标 JD'
      return
    }
    loading.value = true
    error.value = ''
    try {
      report.value = await runJDMatch(
        {
          resume_text: resumeText.value,
          jd_text: jdText.value,
        },
        engine.value,
      )
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '分析失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  function reset() {
    report.value = null
    error.value = ''
  }

  return { resumeText, jdText, report, loading, error, engine, analyze, reset }
})
