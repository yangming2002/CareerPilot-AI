<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>JD 匹配分析</span>
        <div class="header-right">
          <el-radio-group v-model="store.engine" size="small">
            <el-radio-button label="rule">规则引擎</el-radio-button>
            <el-radio-button label="llm">
              <span style="display:flex;align-items:center;gap:4px">
                LLM
                <el-tag size="small" type="warning" effect="dark" style="font-size:10px;padding:0 4px;line-height:16px">BETA</el-tag>
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
      :placeholder="store.engine === 'llm'
        ? '粘贴 JD。LLM 将深度解析岗位要求、技能权重和职责描述。'
        : '粘贴 JD。规则引擎通过关键词白名单和正则进行快速匹配。'"
    />

    <el-button
      type="primary"
      size="large"
      :loading="store.loading"
      style="margin-top: 16px; width: 100%"
      @click="store.analyze()"
    >
      {{ store.engine === 'llm' ? 'LLM 深度分析' : '规则匹配分析' }}
    </el-button>

    <el-alert
      v-if="store.engine === 'llm'"
      title="LLM 模式需要配置 OPENAI_API_KEY 环境变量"
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
}

.header-right {
  display: flex;
  align-items: center;
}
</style>
