<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api/client'

interface Fact { id: number; category: string; content: string; source: string; confidence: string; tags: string; created_at: string }

const facts = ref<Fact[]>([])
const filter = ref('')
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const selection = ref<Fact[]>([])
const editing = ref<Fact | null>(null)
const editContent = ref('')

const categories = [
  { key: '', label: '全部' }, { key: 'skill', label: '技能' }, { key: 'project', label: '项目' },
  { key: 'internship', label: '实习' }, { key: 'education', label: '教育' }, { key: 'weakness', label: '薄弱点' },
]

async function loadFacts() {
  loading.value = true
  try {
    const { data } = await client.get('/api/v1/analysis/user-facts', { params: { category: filter.value || undefined, page: page.value } })
    facts.value = data.items || data
    total.value = data.total || facts.value.length
  } catch { facts.value = []; total.value = 0 }
  finally { loading.value = false }
}

function onFilterChange() { page.value = 1; loadFacts() }

async function batchDelete() {
  if (!selection.value.length) { ElMessage.warning('请先选择记录'); return }
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selection.value.length} 条记录？`, '批量删除', { type: 'warning' })
    await client.post('/api/v1/analysis/user-facts/batch-delete', selection.value.map(f => f.id))
    ElMessage.success('已删除')
    selection.value = []
    loadFacts()
  } catch { }
}

async function deleteFact(id: number) {
  try {
    await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' })
    await client.delete(`/api/v1/analysis/user-facts/${id}`)
    facts.value = facts.value.filter(f => f.id !== id)
    ElMessage.success('已删除')
  } catch { }
}

function startEdit(f: Fact) { editing.value = f; editContent.value = f.content }
async function saveEdit() {
  if (!editing.value) return
  editing.value.content = editContent.value
  editing.value.confidence = 'confirmed'
  editing.value = null
  ElMessage.success('已更新')
}

function toggleConfirm(f: Fact) {
  f.confidence = f.confidence === 'confirmed' ? 'auto' : 'confirmed'
  ElMessage.success(f.confidence === 'confirmed' ? '已确认为高可信事实' : '已取消确认')
}

function handleSelect(rows: Fact[]) { selection.value = rows }

onMounted(loadFacts)
</script>

<template>
  <div class="memory-page">
    <div class="page-header">
      <h1>记忆库</h1>
      <p>系统自动提取的事实。确认为高可信后优先引用。</p>
    </div>
    <div class="toolbar">
      <el-radio-group v-model="filter" size="small" @change="onFilterChange">
        <el-radio-button v-for="c in categories" :key="c.key" :label="c.key" :value="c.key">{{ c.label }}</el-radio-button>
      </el-radio-group>
      <el-button v-if="selection.length" size="small" type="danger" @click="batchDelete" style="margin-left:12px">删除选中({{ selection.length }})</el-button>
    </div>
    <el-table :data="facts" stripe v-loading="loading" @selection-change="handleSelect" style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }"><el-tag size="small" :type="row.category==='skill'?'success':row.category==='weakness'?'danger':row.category==='project'?'warning':'info'">{{ categories.find(c=>c.key===row.category)?.label || row.category }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="280">
        <template #default="{ row }">
          <template v-if="editing?.id === row.id">
            <el-input v-model="editContent" type="textarea" :rows="2" size="small" />
            <el-button size="small" type="primary" @click="saveEdit" style="margin-top:4px">保存</el-button>
            <el-button size="small" @click="editing=null">取消</el-button>
          </template>
          <span v-else>{{ row.content }}</span>
        </template>
      </el-table-column>
      <el-table-column label="可信度" width="90">
        <template #default="{ row }"><el-tag size="small" :type="row.confidence==='confirmed'?'success':'warning'">{{ row.confidence==='confirmed'?'已确认':'自动提取' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" text :type="row.confidence==='confirmed'?'warning':'success'" @click="toggleConfirm(row)">{{ row.confidence==='confirmed'?'取消确认':'确认' }}</el-button>
          <el-button size="small" text @click="startEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="deleteFact(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top:14px;text-align:center" v-if="total > 50">
      <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="prev,pager,next" @change="loadFacts" small />
    </div>
  </div>
</template>

<style scoped>
.memory-page { max-width: 1200px; margin: 0 auto; padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.page-header p { font-size: 13px; color: #6b7280; }
.toolbar { margin-bottom: 16px; display: flex; align-items: center; }
</style>
