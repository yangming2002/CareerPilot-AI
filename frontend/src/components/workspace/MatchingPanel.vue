<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <div>
    <div class="engine-bar">
      <el-radio-group v-model="store.engine" size="small" :disabled="store.loading">
        <el-radio-button label="rule">规则引擎</el-radio-button>
        <el-radio-button label="llm">LLM</el-radio-button>
        <el-radio-button label="graph">
          Agent
          <el-tag size="small" type="warning" effect="dark" class="beta-tag">NEW</el-tag>
        </el-radio-button>
      </el-radio-group>
    </div>

    <el-input
      v-model="store.jdText"
      type="textarea"
      :rows="10"
      resize="none"
      :disabled="store.loading"
      :placeholder="store.engine === 'rule' ? '粘贴 JD。规则引擎通过关键词白名单和正则快速匹配。' : '粘贴 JD。' + (store.engine === 'graph' ? 'Agent 工作流将逐步解析、匹配、校验。' : 'LLM 深度解析岗位要求和技能权重。')"
    />

    <div v-if="store.loading" class="analysis-status">
      <div class="status-line">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ store.statusMessage }}</span>
        <strong>{{ store.elapsedSeconds }}s</strong>
      </div>
      <el-progress
        :percentage="Math.min(100, Math.round((store.elapsedSeconds / (store.engine === 'rule' ? 15 : 60)) * 100))"
        :status="store.isVerySlowLLM ? 'warning' : undefined"
      />
      <div v-if="store.progressSteps.length" class="progress-steps">
        <div v-for="(step, i) in store.progressSteps.slice(-5)" :key="i" class="progress-step">
          <el-icon v-if="i < store.progressSteps.length - 1 || store.progressDone" color="#22c55e"><svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor"/></svg></el-icon>
          <el-icon v-else class="is-loading" color="#2563eb"><Loading /></el-icon>
          <span>{{ step }}</span>
        </div>
      </div>
    </div>

    <div class="button-row">
      <el-button
        type="primary"
        size="large"
        :loading="store.loading"
        :disabled="store.loading"
        @click="store.analyze()"
      >
        {{ store.engine === 'graph' ? 'Agent 工作流分析' : store.engine === 'llm' ? 'LLM 深度分析' : '规则匹配分析' }}
      </el-button>
    </div>

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />
  </div>
</template>

<style scoped>
.engine-bar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.beta-tag {
  padding: 0 4px;
  font-size: 10px;
  line-height: 16px;
  margin-left: 4px;
}

.analysis-status {
  margin-top: 14px;
  padding: 12px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #f8fafc;
}

.status-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #475467;
  font-size: 14px;
  line-height: 1.5;
}

.status-line strong {
  margin-left: auto;
  color: #2563eb;
  font-variant-numeric: tabular-nums;
}

.progress-steps {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e5e7eb;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  font-size: 12px;
  color: #6b7280;
}

.button-row {
  margin-top: 16px;
}

.button-row .el-button {
  width: 100%;
}
</style>
