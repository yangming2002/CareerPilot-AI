<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
const editedResume = ref('')
const showNotice = ref(false)

// Show completion notification when report arrives
watch(() => store.report, (r) => {
  if (r) {
    editedResume.value = r.revised_resume || ''
    if (!r.degraded && store.engine === 'llm') {
      ElMessage.success(`分析完成！匹配度 ${r.match_score} 分`)
    }
  }
})

function handleRetest() {
  if (!editedResume.value.trim()) return
  store.report!.revised_resume = editedResume.value
  store.retestWithRevised()
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
    const resp = await fetch(`http://localhost:8001/api/v1/analysis/export-${fmt}/${id}`, {
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
      v-if="!store.report.degraded && store.engine === 'llm'"
      :title="`LLM 分析完成 | 匹配度 ${store.report.match_score} 分 | 耗时 ${store.elapsedSeconds} 秒`"
      type="success"
      :closable="true"
      show-icon
      style="grid-column: 1 / -1"
    />

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
      <div class="score-number">{{ store.report.match_score }}</div>
      <el-progress
        :percentage="store.report.match_score"
        :color="store.report.match_score >= 70 ? '#22c55e' : store.report.match_score >= 40 ? '#f59e0b' : '#ef4444'"
      />
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
      <template #header>优化建议</template>
      <div v-if="store.report.suggestions.length">
        <div v-for="(s, i) in store.report.suggestions" :key="i" class="suggestion-item">
          <div class="suggestion-header">
            <el-tag
              size="small"
              :type="s.confidence === 'high' ? 'danger' : s.confidence === 'medium' ? 'warning' : ''"
            >
              可信度：{{ s.confidence }}
            </el-tag>
            <span class="suggestion-category">{{ s.category }}</span>
          </div>
          <p class="suggestion-text">{{ s.suggestion }}</p>
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
    <el-card v-if="store.report.revised_resume" shadow="never" class="panel-card" style="grid-column: 1 / -1">
      <template #header>
        <div class="revised-header">
          <span>改写后的简历</span>
          <el-tag size="small" type="success">仅优化表达，未编造经历</el-tag>
        </div>
      </template>
      <p class="revised-hint">
        以下是基于可信建议改写后的简历。你可以手动编辑，然后重新评估匹配度。
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
    </el-card>
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

.score-number {
  margin-bottom: 8px;
  color: #2563eb;
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
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
  margin: 0;
  color: #1f2937;
  font-size: 14px;
  line-height: 1.7;
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
