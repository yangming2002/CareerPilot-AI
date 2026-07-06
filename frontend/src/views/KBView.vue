<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api/client'

const docs = ref<any[]>([])
const loading = ref(false)
const uploading = ref(false)
const kbType = ref('')
const searchQ = ref('')
const searchResults = ref<any[]>([])
const showUpload = ref(false)
const selection = ref<any[]>([])
const page = ref(1)
const total = ref(0)

// Upload form
const uploadContent = ref('')
const uploadFileName = ref('')
const uploadType = ref('custom')

const KB_TYPES = [
  { key: '', label: '全部' },
  { key: 'jd_history', label: 'JD参考' },
  { key: 'resume_methodology', label: '简历方法论' },
  { key: 'tech_learning', label: '技术学习' },
  { key: 'interview_prep', label: '面试准备' },
  { key: 'custom', label: '自定义' },
]

async function loadDocs() {
  loading.value = true
  try {
    const { data } = await client.get('/api/v1/kb/documents', { params: { kb_type: kbType.value || undefined, page: page.value } })
    docs.value = data.items || data
    total.value = data.total || docs.value.length
  } catch { docs.value = []; total.value = 0 }
  finally { loading.value = false }
}

const uploadFile = ref<File | null>(null)

function handleFilePick(e: Event) {
  const input = e.target as HTMLInputElement
  uploadFile.value = input.files?.[0] || null
  if (uploadFile.value && !uploadFileName.value) uploadFileName.value = uploadFile.value.name
}

function clearFile() { uploadFile.value = null; uploadFileName.value = '' }

async function uploadDoc() {
  if (!uploadFile.value && !uploadContent.value.trim()) {
    ElMessage.warning('请上传文件或粘贴文本内容'); return
  }
  uploading.value = true
  try {
    const form = new FormData()
    form.append('kb_type', uploadType.value)
    if (uploadFile.value) {
      form.append('file', uploadFile.value)
      form.append('file_name', uploadFile.value.name)
    } else {
      form.append('content', uploadContent.value)
      form.append('file_name', uploadFileName.value || '手动输入')
    }
    await client.post('/api/v1/kb/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000,
    })
    ElMessage.success('上传成功，已自动分块索引')
    showUpload.value = false; uploadContent.value = ''; uploadFileName.value = ''; uploadFile.value = null
    loadDocs()
  } catch {
    // Keep form open on error so user can retry
  } finally { uploading.value = false }
}

async function deleteDoc(id: number) {
  try {
    await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' })
    await client.delete(`/api/v1/kb/documents/${id}`)
    ElMessage.success('已删除')
    loadDocs()
  } catch { }
}

async function batchDeleteDocs() {
  if (!selection.value.length) { ElMessage.warning('请先选择'); return }
  try {
    await ElMessageBox.confirm(`确定删除 ${selection.value.length} 条？`, '批量删除', { type: 'warning' })
    await client.post('/api/v1/kb/documents/batch-delete', selection.value.map((d: any) => d.id))
    ElMessage.success('已删除')
    selection.value = []
    loadDocs()
  } catch { }
}

function handleSelect(rows: any[]) { selection.value = rows }

function onTypeChange() { page.value = 1; loadDocs() }

async function search() {
  if (!searchQ.value.trim()) return
  try {
    const { data } = await client.get('/api/v1/kb/search', { params: { q: searchQ.value, kb_type: kbType.value } })
    searchResults.value = data
  } catch { searchResults.value = [] }
}

onMounted(loadDocs)
</script>

<template>
  <div class="kb-page">
    <div class="kb-header">
      <div>
        <h1>知识库</h1>
        <p>上传文档自动分块索引，Agent 分析时按需检索引用。</p>
      </div>
      <el-button type="primary" @click="showUpload = !showUpload">{{ showUpload ? '取消' : '上传文档' }}</el-button>
    </div>

    <!-- Upload -->
    <div v-if="showUpload" class="upload-card">
      <el-form label-position="top" size="default">
        <el-row :gutter="12">
          <el-col :span="6">
            <el-form-item label="知识库类型">
              <el-select v-model="uploadType" style="width:100%">
                <el-option v-for="t in KB_TYPES.filter(t=>t.key)" :key="t.key" :label="t.label" :value="t.key" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="文件名">
              <el-input v-model="uploadFileName" placeholder="例如：STAR方法论指南" />
            </el-form-item>
          </el-col>
          <el-col :span="6" style="display:flex;align-items:flex-end;padding-bottom:16px">
            <el-button type="primary" :loading="uploading" @click="uploadDoc" style="width:100%">上传并索引</el-button>
          </el-col>
        </el-row>
        <el-form-item label="上传文件或粘贴内容">
          <div style="display:flex;gap:12px;margin-bottom:10px">
            <label>
              <el-button size="default" @click="($refs.fileInput as any)?.click()">选择文件</el-button>
              <input ref="fileInput" type="file" accept=".pdf,.docx,.doc,.txt,.md" hidden @change="handleFilePick" />
            </label>
            <span v-if="uploadFile" class="file-name">
              📄 {{ uploadFile.name }}
              <button class="clear-file-btn" @click="clearFile">✕</button>
            </span>
          </div>
          <el-input v-model="uploadContent" type="textarea" :rows="6" placeholder="或直接粘贴文档内容..." />
        </el-form-item>
      </el-form>
    </div>

    <!-- Search -->
    <div class="search-bar">
      <el-input v-model="searchQ" placeholder="搜索知识库..." @keyup.enter="search" clearable>
        <template #append><el-button @click="search">搜索</el-button></template>
      </el-input>
      <el-select v-model="kbType" @change="onTypeChange" style="width:140px;margin-left:8px" placeholder="类型">
        <el-option v-for="t in KB_TYPES" :key="t.key" :label="t.label" :value="t.key" />
      </el-select>
    </div>

    <!-- Search Results -->
    <div v-if="searchResults.length" class="search-results">
      <h3>搜索结果</h3>
      <div v-for="(r, i) in searchResults" :key="i" class="search-item">
        <div class="search-score">相关度 {{ r.score }}</div>
        <p>{{ r.text }}</p>
      </div>
    </div>

    <!-- Doc List -->
    <div style="margin-bottom:10px" v-if="selection.length">
      <el-button size="small" type="danger" @click="batchDeleteDocs">删除选中({{ selection.length }})</el-button>
    </div>
    <el-table :data="docs" stripe v-loading="loading" @selection-change="handleSelect" style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">{{ KB_TYPES.find(t=>t.key===row.kb_type)?.label || row.kb_type }}</template>
      </el-table-column>
      <el-table-column prop="file_name" label="文件名" min-width="200" />
      <el-table-column label="分块" width="80">
        <template #default="{ row }"><el-tag size="small" round>{{ row.chunk_count }} 块</el-tag></template>
      </el-table-column>
      <el-table-column label="预览" min-width="300">
        <template #default="{ row }">{{ row.preview }}</template>
      </el-table-column>
      <el-table-column label="时间" width="160">
        <template #default="{ row }">{{ row.created_at?.slice(0,16)?.replace('T',' ') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button size="small" text type="danger" @click="deleteDoc(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !docs.length" description="知识库为空，上传第一篇文档吧" />
    <div style="margin-top:14px;text-align:center" v-if="total > 50">
      <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="prev,pager,next" @change="loadDocs" small />
    </div>
  </div>
</template>

<style scoped>
.kb-page { max-width: 1200px; margin: 0 auto; padding: 32px; }
.kb-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.kb-header h1 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.kb-header p { font-size: 13px; color: #6b7280; }

.upload-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 20px; }

.search-bar { display: flex; margin-bottom: 20px; }

.search-results { margin-bottom: 20px; }
.search-results h3 { font-size: 14px; color: #374151; margin-bottom: 10px; }
.search-item { padding: 10px 14px; background: #f9fafb; border-radius: 8px; margin-bottom: 8px; }
.search-score { font-size: 11px; color: #2563eb; font-weight: 600; margin-bottom: 4px; }
.file-name { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #374151; }
.clear-file-btn { border: none; background: #fee2e2; color: #ef4444; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 11px; display: flex; align-items: center; justify-content: center; }

.search-item p { font-size: 13px; color: #374151; line-height: 1.6; }
</style>
