<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <section v-if="store.report" class="report-grid">
    <!-- Degraded Banner -->
    <el-alert
      v-if="store.report.degraded"
      :title="store.report.degraded_reason || 'LLM 分析降级'"
      type="warning"
      :closable="false"
      show-icon
      style="grid-column: 1 / -1; margin-bottom: 4px"
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
      <p style="margin-top: 12px; color: #667085; line-height: 1.7">
        {{ store.report.jd_summary }}
      </p>
    </el-card>

    <!-- Skill Gaps -->
    <el-card shadow="never" class="panel-card">
      <template #header>技能缺口分析</template>
      <div v-if="store.report.skill_gaps.length">
        <div
          v-for="gap in store.report.skill_gaps"
          :key="gap.skill"
          class="gap-row"
        >
          <el-tag
            :type="gap.user_has ? 'success' : 'danger'"
            size="small"
          >
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
        <div
          v-for="(s, i) in store.report.suggestions"
          :key="i"
          class="suggestion-item"
        >
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
