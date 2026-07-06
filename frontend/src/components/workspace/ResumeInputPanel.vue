<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'
import { uploadAndParseResume, type ParsedResumeFields } from '@/api'

const store = useAnalysisStore()
const uploading = ref(false)
const fileInput = ref<HTMLInputElement>()
const parsedFields = ref<ParsedResumeFields | null>(null)
const showFields = ref(false)

const KEY_FIELDS = [
  { key: 'skills', label: '专业技能', icon: '⚡' },
  { key: 'education', label: '教育背景', icon: '🎓' },
  { key: 'projects', label: '项目经历', icon: '📦', critical: true, hint: '缺少项目经历会显著降低竞争力' },
  { key: 'internships', label: '实习经历', icon: '💼', optional: true, hint: '有实习经验是加分项' },
  { key: 'campus_experience', label: '校园经历', icon: '🏫' },
  { key: 'self_evaluation', label: '自我评价', icon: '📝' },
]

function isEmpty(val: unknown): boolean {
  if (Array.isArray(val)) return val.length === 0
  return !val
}

async function handleUpload(file: File) {
  uploading.value = true
  try {
    const result = await uploadAndParseResume(file)
    parsedFields.value = result
    showFields.value = true
    const parts: string[] = []
    if (result.name) parts.push(`${result.name}`)
    if (result.email) parts.push(`${result.email}`)
    if (result.phone) parts.push(`${result.phone}`)
    if (result.education.length) {
      parts.push('')
      result.education.forEach(e => parts.push(`${e.school} | ${e.degree} | ${e.major} ${e.year || ''}`))
    }
    if (result.skills.length) parts.push(`\n${result.skills.join(' · ')}`)
    if (result.internships.length) {
      parts.push('')
      result.internships.forEach(i => parts.push(`${i.company} | ${i.role} | ${i.duration || ''}`))
    }
    if (result.projects.length) {
      parts.push('')
      result.projects.forEach(p => {
        parts.push(p.name)
        if (p.description) parts.push(`  ${p.description}`)
      })
    }
    store.resumeText = parts.join('\n')
    ElMessage.success('解析完成')
  } catch { /* handled by interceptor */ }
  finally { uploading.value = false }
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) handleUpload(file)
  input.value = ''
}
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <span>简历</span>
      <el-button size="small" :loading="uploading" round @click="fileInput?.click()">上传 PDF/DOCX</el-button>
      <input ref="fileInput" type="file" accept=".pdf,.docx,.doc,.txt" hidden @change="handleFileInput" />
    </div>

    <div v-if="showFields && parsedFields" class="fields-box">
      <div v-for="f in KEY_FIELDS" :key="f.key" class="field-row">
        <span class="field-icon">{{ f.icon }}</span>
        <span class="field-label">{{ f.label }}</span>
        <el-tag v-if="isEmpty(parsedFields[f.key as keyof ParsedResumeFields])" size="small"
          :type="f.critical ? 'danger' : f.optional ? 'warning' : 'info'" effect="plain" round>
          {{ f.critical ? '建议补充' : f.optional ? '加分项' : '未填写' }}
        </el-tag>
        <el-tag v-else size="small" type="success" effect="plain" round>已识别</el-tag>
        <span v-if="f.hint && isEmpty(parsedFields[f.key as keyof ParsedResumeFields])" class="field-hint">{{ f.hint }}</span>
      </div>
    </div>

    <el-input
      v-model="store.resumeText"
      type="textarea"
      :rows="showFields ? 5 : 14"
      resize="none"
      placeholder="粘贴简历全文，或点击「上传 PDF/DOCX」"
    />
  </div>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}

.panel-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; font-weight: 600; font-size: 15px; color: #111827;
}

.fields-box {
  margin-bottom: 12px; padding: 12px 14px;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px;
}

.field-row {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 0; font-size: 13px; flex-wrap: wrap;
}

.field-icon { font-size: 14px; }

.field-label { color: #374151; font-weight: 500; }

.field-hint {
  width: 100%; margin-left: 24px;
  font-size: 11px; color: #ef4444; line-height: 1.5;
}

.upload-btn { cursor: pointer; }
</style>
