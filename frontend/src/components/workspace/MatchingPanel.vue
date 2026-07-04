<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>JD 匹配分析</span>
        <div class="header-right">
          <el-radio-group v-model="store.engine" size="small" :disabled="store.loading">
            <el-radio-button label="rule">规则引擎</el-radio-button>
            <el-radio-button label="llm">
              <span class="llm-label">
                LLM
                <el-tag size="small" type="warning" effect="dark" class="beta-tag">BETA</el-tag>
              </span>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </template>

    <el-input
      v-model="store.jdText"
      type="textarea"
      :rows="12"
      resize="none"
      :disabled="store.loading"
      :placeholder="store.engine === 'llm'
        ? '粘贴 JD。LLM 会深度解析岗位要求、技能权重和职责描述。'
        : '粘贴 JD。规则引擎会通过关键词白名单和正则进行快速匹配。'"
    />

    <div v-if="store.loading" class="analysis-status">
      <div class="status-line">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ store.statusMessage }}</span>
        <strong>{{ store.elapsedSeconds }}s</strong>
      </div>
      <el-progress
        :percentage="Math.min(100, Math.round((store.elapsedSeconds / (store.engine === 'llm' ? 45 : 15)) * 100))"
        :status="store.isVerySlowLLM ? 'warning' : undefined"
      />
      <el-button
        v-if="store.engine === 'llm' && store.isSlowLLM"
        size="small"
        plain
        type="warning"
        class="fallback-button"
        @click="store.cancelAndRunRule()"
      >
        停止等待，改用规则引擎
      </el-button>
    </div>

    <div class="button-row">
      <el-button
        type="primary"
        size="large"
        :loading="store.loading"
        :disabled="store.loading"
        @click="store.analyze()"
      >
        {{ store.engine === 'llm' ? 'LLM 深度分析' : '规则匹配分析' }}
      </el-button>
    </div>

    <el-alert
      v-if="store.engine === 'llm' && !store.loading"
      title="LLM 模式可能受网络和模型响应速度影响；如需快速结果，可切换规则引擎。"
      type="info"
      :closable="false"
      show-icon
      style="margin-top: 12px"
    />

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />
  </el-card>
</template>

<style scoped>
.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
}

.llm-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.beta-tag {
  padding: 0 4px;
  font-size: 10px;
  line-height: 16px;
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

.fallback-button {
  margin-top: 10px;
}

.button-row {
  margin-top: 16px;
}

.button-row .el-button {
  width: 100%;
}
</style>
