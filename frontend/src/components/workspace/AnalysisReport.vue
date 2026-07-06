<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
const editedResume = ref('')
const shownAnalysisDialog = ref(false)
const backendElapsed = ref('')

// Show completion dialog only when analysis first completes (not on resume rewrite)
watch(() => store.report, (r) => {
  if (r) {
    editedResume.value = r.revised_resume || ''

    // Only show analysis dialog once per analysis
    if (!shownAnalysisDialog.value) {
      shownAnalysisDialog.value = true
      const gaps = r.skill_gaps || []
      const covered = gaps.filter(g => g.user_has).length
      const total = gaps.length
      const log = r.progress_log || []
      for (let i = log.length - 1; i >= 0; i--) {
        const m = log[i].match(/\(([\d.]+)s\)/)
        if (m) { backendElapsed.value = m[1] + 's'; break }
      }

      const msg = r.degraded
        ? `<p style='color:#f59e0b'>⚠ ${r.degraded_reason || '分析降级完成'}</p>`
        : `<p>匹配度 <b style='color:#2563eb;font-size:24px'>${r.match_score}</b> 分</p>
           <p>技能覆盖 <b>${covered}/${total}</b> | 优化建议 <b>${(r.suggestions||[]).length}</b> 条</p>
           <p style='color:#667085;font-size:13px'>耗时 ${store.elapsedSeconds}s</p>`

      ElMessageBox.alert(msg, r.degraded ? '分析完成（降级）' : '分析完成', {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '查看详情',
        type: r.degraded ? 'warning' : 'success',
      }).then(() => {
        setTimeout(() => {
          const el = document.querySelector('.report-grid')
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 200)
      }).catch(() => {})
    }
  }
})

// Reset dialog flag when analysis starts loading
watch(() => store.loading, (l) => {
  if (l) shownAnalysisDialog.value = false
})

function handleRetest() {
  if (!editedResume.value.trim()) return
  store.report!.revised_resume = editedResume.value
  store.retestWithRevised()
}

async function handleAction(action: string) {
  if (action === 'rewrite') store.rewriteResume()
  else if (action === 'save') {
    try {
      const { createApplication } = await import('@/api')
      await createApplication({
        company: store.jdCompany || '未填写',
        position: store.jdPosition || '未填写',
        status: '已投递',
      })
      ElMessage.success('已保存为投递记录')
    } catch { }
  }
  else if (action === 'export') handleExport('md')
  else if (action === 'learn') {
    const gapEl = document.querySelector('.panel-card')
    if (gapEl) gapEl.scrollIntoView({ behavior: 'smooth' })
  }
  else if (action === 'retry') { store.reset(); window.scrollTo({ top: 0, behavior: 'smooth' }) }
}

function handleSave() {
  const text = editedResume.value || store.report?.revised_resume || ''
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('改写后的简历已复制到剪贴板')
  }).catch(() => {
    ElMessage.info('请手动复制改写后的简历')
  })
}

async function handleExport(fmt: 'md' | 'pdf') {
  const id = store.report?.id
  if (!id) return
  const token = localStorage.getItem('token')
  try {
    const base = import.meta.env.PROD ? '' : 'http://localhost:8001'
    const resp = await fetch(`${base}/api/v1/analysis/export-${fmt}/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '导出失败' }))
      ElMessage.error(err.detail || '导出失败')
      return
    }
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `revised_resume.${fmt}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`已导出为 ${fmt.toUpperCase()} 文件`)
  } catch {
    ElMessage.error('导出失败，请检查网络连接')
  }
}
</script>

<template>
  <section v-if="store.report" class="report-grid">
    <!-- Completion Notice -->
    <el-alert
      v-if="!store.report.degraded"
      :title="`分析完成 | 匹配度 ${store.report.match_score} 分`"
      type="success"
      :closable="true"
      show-icon
      style="grid-column: 1 / -1"
    />

    <!-- Pre-Check -->
    <div v-if="store.report.pre_check?.length" class="precheck-card" style="grid-column:1/-1">
      <div class="precheck-title">Agent 预检查</div>
      <div v-for="(c, i) in store.report.pre_check" :key="i" class="precheck-item" :class="c.type">
        <span class="precheck-icon">{{ c.type === 'ok' ? '✅' : c.type === 'warning' ? '⚠️' : 'ℹ️' }}</span>
        {{ c.msg }}
      </div>
    </div>

    <!-- Degraded Banner -->
    <el-alert
      v-if="store.report.degraded"
      :title="store.report.degraded_reason || 'LLM 分析降级'"
      type="warning"
      :closable="false"
      show-icon
      style="grid-column: 1 / -1"
    />

    <!-- Progress Log -->
    <el-card v-if="store.report.progress_log?.length" shadow="never" class="panel-card" style="grid-column: 1 / -1">
      <template #header>分析过程 ({{ store.report.progress_log.length }} 步)</template>
      <ol class="progress-list">
        <li v-for="(step, i) in store.report.progress_log" :key="i">{{ step }}</li>
      </ol>
    </el-card>

    <!-- Match Score -->
    <el-card shadow="never" class="panel-card score-card">
      <template #header>匹配得分</template>
      <div class="score-row">
        <div class="score-main">
          <div class="score-number">{{ store.report.match_score }}</div>
          <span class="score-label">LLM 综合评分</span>
        </div>
        <div class="score-refs" v-if="store.report.nlp_score">
          <div class="ref-item">
            <span class="ref-val">{{ store.report.nlp_score }}</span>
            <span class="ref-label">NLP 客观分</span>
          </div>
          <div class="ref-item">
            <span class="ref-val">{{ store.report.tfidf_score }}</span>
            <span class="ref-label">TF-IDF 相似度</span>
          </div>
          <div class="ref-item">
            <span class="ref-val">{{ store.report.keyword_score }}</span>
            <span class="ref-label">关键词覆盖率</span>
          </div>
        </div>
      </div>
      <el-progress
        :percentage="store.report.match_score"
        :color="store.report.match_score >= 70 ? '#22c55e' : store.report.match_score >= 40 ? '#f59e0b' : '#ef4444'"
      />
    </el-card>

    <!-- Similar JDs from RAG -->
    <el-card v-if="store.report.similar_jds?.length" shadow="never" class="panel-card score-card">
      <template #header>相关历史岗位</template>
      <div class="similar-jd-list">
        <div v-for="(jd, i) in store.report.similar_jds.slice(0, 5)" :key="i" class="similar-jd-item">
          <span class="similar-jd-company">{{ jd.company || '未知' }}</span>
          <span class="similar-jd-pos">{{ jd.position || '未知岗位' }}</span>
          <el-tag size="small" :type="(jd.match_score||0) >= 70 ? 'success' : (jd.match_score||0) >= 40 ? 'warning' : 'danger'">
            匹配{{ jd.match_score || 0 }}分
          </el-tag>
          <span class="similar-jd-sim">相似度 {{ ((jd.score || 0) * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </el-card>

    <!-- Skill Gaps -->
    <el-card shadow="never" class="panel-card">
      <template #header>技能缺口分析</template>
      <div v-if="store.report.skill_gaps.length">
        <div v-for="gap in store.report.skill_gaps" :key="gap.skill" class="gap-row">
          <el-tag :type="gap.user_has ? 'success' : 'danger'" size="small">
            {{ gap.user_has ? '已覆盖' : '缺失' }}
          </el-tag>
          <span class="gap-skill">{{ gap.skill }}</span>
          <span class="gap-note">{{ gap.note }}</span>
        </div>
      </div>
      <p v-else class="no-data">未检测到技能需求或简历技能信息不足</p>
    </el-card>

    <!-- Suggestions -->
    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>优化建议</span>
        <el-tag size="small" type="info" style="margin-left:8px">证据链</el-tag>
      </template>
      <div v-if="store.report.suggestions.length">
        <div v-for="(s, i) in store.report.suggestions" :key="i" class="suggestion-item">
          <p class="suggestion-text">{{ s.suggestion }}</p>
          <div class="evidence-row">
            <span class="evidence-label">依据</span>
            <span v-if="s.grounded_in" class="evidence-source" :title="s.grounded_in">
              {{ s.grounded_in.slice(0, 80) }}{{ s.grounded_in.length > 80 ? '…' : '' }}
            </span>
            <span v-else class="evidence-source none">未标注出处</span>
            <el-tag size="small" :type="s.confidence === 'high' ? 'success' : s.confidence === 'medium' ? 'warning' : 'info'">
              {{ s.confidence === 'high' ? '高可信' : s.confidence === 'medium' ? '中可信' : '低可信' }}
            </el-tag>
            <el-tag size="small" type="info">{{ s.category }}</el-tag>
          </div>
        </div>
      </div>
      <p v-else class="no-data">暂无优化建议</p>
    </el-card>

    <!-- Integrity Checks -->
    <el-card shadow="never" class="panel-card">
      <template #header>完整性检查</template>
      <div v-if="store.report.integrity_checks.length">
        <el-alert
          v-for="(check, i) in store.report.integrity_checks"
          :key="i"
          :title="check.description"
          :type="check.severity === 'pass' ? 'success' : check.severity === 'warning' ? 'warning' : 'error'"
          :closable="false"
          show-icon
          style="margin-bottom: 8px"
        >
          <template v-if="check.detail" #default>
            <p style="margin: 4px 0 0; font-size: 13px">{{ check.detail }}</p>
          </template>
        </el-alert>
      </div>
      <p v-else class="no-data">完整性检查通过</p>
    </el-card>

    <!-- Revised Resume -->
    <el-card shadow="never" class="panel-card" style="grid-column: 1 / -1">
      <template #header>
        <div class="revised-header">
          <span>改写简历</span>
          <el-tag v-if="store.report.revised_resume" size="small" type="success">仅优化表达，未编造经历</el-tag>
        </div>
      </template>

      <!-- Not yet generated -->
      <div v-if="!store.report.revised_resume && !store.rewriteLoading">
        <p class="revised-hint">
          匹配分析完成。如需改写简历，点击下方按钮生成优化后的版本。
        </p>
        <el-button
          type="primary"
          :loading="store.rewriteLoading"
          @click="store.rewriteResume()"
        >
          生成改写简历
        </el-button>
      </div>

      <!-- Generating -->
      <div v-if="store.rewriteLoading" class="loading-rewrite">
        <el-icon class="is-loading"><svg viewBox="0 0 24 24"><path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z" fill="currentColor"/></svg></el-icon>
        <span>正在生成改写后的简历...</span>
      </div>

      <!-- Generated -->
      <template v-if="store.report.revised_resume">
        <p class="revised-hint">
          以下是基于可信建议改写后的简历。可手动编辑，然后重新评估匹配度。
        </p>
        <el-input
          v-model="editedResume"
          type="textarea"
          :rows="14"
          resize="vertical"
          placeholder="改写后的简历..."
        />
        <div class="revised-actions">
          <el-button type="primary" :loading="store.loading" @click="handleRetest">
            重新评估匹配度
          </el-button>
          <el-button @click="handleSave">复制到剪贴板</el-button>
          <el-button v-if="store.report?.id" @click="handleExport('md')">导出 Markdown</el-button>
          <el-button v-if="store.report?.id" @click="handleExport('pdf')">导出 PDF</el-button>
        </div>
      </template>
    </el-card>
    <!-- Next Actions -->
    <div v-if="store.report.next_actions?.length" class="actions-card" style="grid-column:1/-1">
      <div class="actions-title">Agent 建议下一步</div>
      <div class="actions-grid">
        <button v-for="a in store.report.next_actions" :key="a.action" class="action-btn" @click="handleAction(a.action)">
          <span class="action-icon">{{ a.icon }}</span>
          <div>
            <div class="action-label">{{ a.label }}</div>
            <div class="action-desc">{{ a.desc }}</div>
          </div>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-top: 18px;
}

.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.score-card {
  grid-column: 1 / -1;
}

.score-row {
  display: flex;
  align-items: flex-start;
  gap: 40px;
  margin-bottom: 16px;
}

.score-main {
  text-align: center;
}

.score-number {
  color: #2563eb;
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
}

.score-label {
  display: block;
  margin-top: 4px;
  color: #9ca3af;
  font-size: 12px;
}

.score-refs {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.ref-item {
  text-align: center;
}

.ref-val {
  display: block;
  color: #374151;
  font-size: 22px;
  font-weight: 700;
}

.ref-label {
  display: block;
  margin-top: 2px;
  color: #9ca3af;
  font-size: 11px;
}

.gap-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.gap-row:last-child {
  border-bottom: none;
}

.gap-skill {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.gap-note {
  color: #667085;
  font-size: 12px;
  margin-left: auto;
}

.suggestion-item {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.suggestion-category {
  font-size: 13px;
  color: #667085;
}

.suggestion-text {
  margin: 0 0 8px;
  color: #1f2937;
  font-size: 14px;
  line-height: 1.7;
}

.evidence-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #f0f9ff;
  border-radius: 6px;
  font-size: 12px;
}

.evidence-label {
  color: #2563eb;
  font-weight: 600;
  white-space: nowrap;
}

.evidence-source {
  flex: 1;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-source.none {
  color: #ef4444;
  font-style: italic;
}

.progress-list {
  margin: 0;
  padding-left: 20px;
  color: #475467;
  font-size: 13px;
  line-height: 2;
}

.revised-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.revised-hint {
  margin: 0 0 12px;
  color: #667085;
  font-size: 13px;
  line-height: 1.6;
}

.loading-rewrite {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #667085;
  font-size: 14px;
}

.precheck-card {
  background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px; padding: 16px;
}
.precheck-title { font-weight: 700; font-size: 13px; color: #92400e; margin-bottom: 8px; }
.precheck-item { font-size: 13px; padding: 3px 0; color: #78350f; display: flex; align-items: center; gap: 6px; }
.precheck-item.ok { color: #166534; }
.precheck-icon { flex-shrink: 0; }

.actions-card {
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 16px;
}
.actions-title { font-weight: 700; font-size: 13px; color: #0369a1; margin-bottom: 10px; }
.actions-grid { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; background: #fff; border: 1px solid #e0f2fe;
  border-radius: 10px; cursor: pointer; text-align: left;
  transition: all .15s; flex: 1; min-width: 200px;
}
.action-btn:hover { border-color: #0ea5e9; box-shadow: 0 2px 8px rgba(14,165,233,.12); }
.action-icon { font-size: 20px; flex-shrink: 0; }
.action-label { font-size: 13px; font-weight: 600; color: #0c4a6e; }
.action-desc { font-size: 11px; color: #6b7280; margin-top: 2px; }

.similar-jd-list { display: flex; flex-direction: column; gap: 8px; }
.similar-jd-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.similar-jd-item:last-child { border: none; }
.similar-jd-company { font-weight: 600; color: #1f2937; min-width: 100px; }
.similar-jd-pos { color: #6b7280; flex: 1; }
.similar-jd-sim { color: #9ca3af; font-size: 11px; margin-left: auto; }

.revised-actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}

.no-data {
  color: #667085;
  text-align: center;
  padding: 20px;
}

@media (max-width: 900px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
