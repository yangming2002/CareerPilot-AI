<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <div class="panel">
    <el-form label-position="top" size="default">
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="公司名称">
            <el-input v-model="store.jdCompany" placeholder="例如：科大讯飞" :disabled="store.loading" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="岗位名称">
            <el-input v-model="store.jdPosition" placeholder="例如：AI应用开发实习生" :disabled="store.loading" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <el-input
      v-model="store.jdText"
      type="textarea"
      :rows="12"
      resize="none"
      :disabled="store.loading"
      placeholder="粘贴 JD。Agent 将逐步解析岗位要求、匹配技能、生成建议并校验真实性。"
    />

    <div v-if="store.loading" class="trace-box">
      <div class="trace-head">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>Agent 正在执行...</span>
        <strong>{{ store.elapsedSeconds }}s</strong>
      </div>
      <div class="trace-steps">
        <div v-for="(step, i) in store.progressSteps.slice(-10)" :key="i" class="trace-step">
          <span class="trace-dot" :class="{ done: i < store.progressSteps.length - 1 || store.progressDone }">✓</span>
          <span class="trace-text">{{ step }}</span>
        </div>
      </div>
      <p v-if="!store.progressSteps.length" class="trace-wait">准备中...</p>
    </div>

    <el-button
      type="primary" size="large" :loading="store.loading" :disabled="store.loading"
      class="analyze-btn" @click="store.analyze()"
    >开始分析</el-button>

    <el-alert v-if="store.error" :title="store.error" type="error" show-icon :closable="false" class="err-alert" />
  </div>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}

.analyze-btn {
  width: 100%;
  margin-top: 16px;
  height: 44px;
  font-weight: 600;
  border-radius: 10px;
}

.trace-box {
  margin-top: 14px;
  padding: 14px 16px;
  background: #0f172a;
  border-radius: 10px;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
}

.trace-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #94a3b8; margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #1e293b;
}

.trace-head strong { margin-left: auto; color: #38bdf8; }

.trace-steps { max-height: 280px; overflow-y: auto; }

.trace-step {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 3px 0; font-size: 12px; color: #94a3b8; line-height: 1.6;
}

.trace-dot {
  width: 18px; height: 18px; border-radius: 50%;
  background: #1e293b; color: #1e293b;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; flex-shrink: 0; margin-top: 1px;
}

.trace-dot.done { background: #22c55e; color: #fff; }

.trace-text { word-break: break-all; }

.trace-wait { font-size: 12px; color: #64748b; text-align: center; padding: 20px; }

.err-alert { margin-top: 12px; }
</style>
