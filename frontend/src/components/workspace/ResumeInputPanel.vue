<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'
import { uploadAndParseResume, type ParsedResumeFields } from '@/api'

const store = useAnalysisStore()
const uploading = ref(false)
const parsedFields = ref<ParsedResumeFields | null>(null)
const showFields = ref(false)

const KEY_FIELDS = [
  { key: 'projects', label: '项目经历', desc: '缺少项目经历会显著降低竞争力，建议至少补充 1-2 个课程项目或个人项目。' },
  { key: 'internships', label: '实习经历', desc: '有实习经验是加分项，没有也不是硬伤，可在校园经历中突出实践能力。' },
  { key: 'skills', label: '专业技能', desc: '' },
  { key: 'education', label: '教育背景', desc: '' },
  { key: 'campus_experience', label: '校园经历', desc: '' },
  { key: 'self_evaluation', label: '自我评价', desc: '' },
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
    // Auto-fill the resume textarea with LLM raw summary or reconstructed text
    const parts: string[] = []
    if (result.name) parts.push(`姓名: ${result.name}`)
    if (result.email) parts.push(`邮箱: ${result.email}`)
    if (result.phone) parts.push(`电话: ${result.phone}`)
    if (result.education.length) {
      parts.push('\n教育背景:')
      result.education.forEach(e => parts.push(`  ${e.school} | ${e.degree} | ${e.major} | ${e.year || ''}`))
    }
    if (result.skills.length) parts.push(`\n技能: ${result.skills.join('、')}`)
    if (result.internships.length) {
      parts.push('\n实习/工作经历:')
      result.internships.forEach(i => parts.push(`  ${i.company} | ${i.role} | ${i.duration || ''}\n  ${i.description || ''}`))
    }
    if (result.projects.length) {
      parts.push('\n项目经历:')
      result.projects.forEach(p => {
        parts.push(`  ${p.name}${p.role ? ' | ' + p.role : ''}`)
        if (p.description) parts.push(`  ${p.description}`)
      })
    }
    if (result.campus_experience.length) {
      parts.push('\n校园经历:')
      result.campus_experience.forEach(c => parts.push(`  ${c.org} | ${c.role}\n  ${c.description || ''}`))
    }
    if (result.self_evaluation) parts.push(`\n自我评价: ${result.self_evaluation}`)
    store.resumeText = parts.join('\n')
    ElMessage.success('简历解析完成，字段已自动填充到文本框。')
  } catch {
    // Error handled by interceptor
  } finally {
    uploading.value = false
  }
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) handleUpload(file)
  input.value = ''
}

function clearFields() {
  parsedFields.value = null
  showFields.value = false
}
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>简历内容</span>
        <div class="header-right">
          <label class="upload-btn">
            <el-button size="small" :loading="uploading" @click="($refs.fileInput as HTMLInputElement)?.click()">
              {{ uploading ? '解析中...' : '上传简历' }}
            </el-button>
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              style="display:none"
              @change="handleFileInput"
            />
          </label>
          <el-tag size="small" type="warning">敏感数据</el-tag>
        </div>
      </div>
    </template>

    <!-- Structured Fields -->
    <div v-if="showFields && parsedFields" class="fields-card">
      <div class="fields-header">
        <span>解析结果</span>
        <el-button size="small" text @click="clearFields">收起</el-button>
      </div>
      <div v-for="f in KEY_FIELDS" :key="f.key" class="field-row">
        <div class="field-label">
          <span>{{ f.label }}</span>
          <el-tag
            v-if="isEmpty(parsedFields[f.key as keyof ParsedResumeFields])"
            :type="f.key === 'projects' ? 'danger' : f.key === 'internships' ? 'warning' : 'info'"
            size="small"
          >
            {{ f.key === 'projects' || f.key === 'internships' ? '建议补充' : '未填写' }}
          </el-tag>
          <el-tag v-else size="small" type="success">{{ '已识别' }}</el-tag>
        </div>
        <p v-if="f.desc && isEmpty(parsedFields[f.key as keyof ParsedResumeFields])" class="field-hint">{{ f.desc }}</p>
        <div v-if="f.key === 'skills' && parsedFields.skills.length" class="field-tags">
          <el-tag v-for="s in parsedFields.skills" :key="s" size="small" style="margin: 2px 4px 2px 0">{{ s }}</el-tag>
        </div>
        <div v-if="f.key === 'education' && parsedFields.education.length" class="mini-list">
          <div v-for="(e, i) in parsedFields.education" :key="i">{{ e.school }} | {{ e.degree }} | {{ e.major }} {{ e.year ? '| ' + e.year : '' }}</div>
        </div>
        <div v-if="f.key === 'projects' && parsedFields.projects.length" class="mini-list">
          <div v-for="(p, i) in parsedFields.projects" :key="i">
            <strong>{{ p.name }}</strong>{{ p.role ? ' | ' + p.role : '' }}
            <div v-if="p.description" class="project-desc">{{ p.description }}</div>
          </div>
        </div>
        <div v-if="f.key === 'internships' && parsedFields.internships.length" class="mini-list">
          <div v-for="(i, j) in parsedFields.internships" :key="j">{{ i.company }} | {{ i.role }} {{ i.duration ? '| ' + i.duration : '' }}</div>
        </div>
        <div v-if="f.key === 'campus_experience' && parsedFields.campus_experience.length" class="mini-list">
          <div v-for="(c, k) in parsedFields.campus_experience" :key="k">{{ c.org }}{{ c.role ? ' | ' + c.role : '' }}</div>
        </div>
      </div>
    </div>

    <!-- Textarea -->
    <el-input
      v-model="store.resumeText"
      type="textarea"
      :rows="showFields ? 6 : 14"
      resize="none"
      placeholder="粘贴简历全文，或点击「上传简历」上传 PDF / DOCX / TXT 文件。Agent 会自动提取技能、项目和教育信息。"
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
  gap: 8px;
}

.upload-btn {
  cursor: pointer;
}

.fields-card {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fafbfc;
}

.fields-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.field-row {
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.field-row:last-child {
  border-bottom: none;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #374151;
}

.field-hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #ef4444;
  line-height: 1.5;
}

.field-tags {
  margin-top: 4px;
}

.mini-list {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
}

.project-desc {
  margin-top: 2px;
  padding-left: 8px;
  border-left: 2px solid #d1d5db;
  white-space: pre-line;
  color: #9ca3af;
  font-size: 11px;
}
</style>
