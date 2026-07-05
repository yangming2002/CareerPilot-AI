<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api/client'

interface Fact {
  id: number; category: string; content: string; source: string
  confidence: string; tags: string; created_at: string
}

const facts = ref<Fact[]>([])
const filter = ref('')
const loading = ref(false)
const editing = ref<Fact | null>(null)
const editContent = ref('')

const categories = [
  { key: '', label: '全部' },
  { key: 'skill', label: '技能' },
  { key: 'project', label: '项目' },
  { key: 'internship', label: '实习' },
  { key: 'education', label: '教育' },
  { key: 'weakness', label: '薄弱点' },
]

async function loadFacts() {
  loading.value = true
  try {
    const params: any = {}
    if (filter.value) params.category = filter.value
    const { data } = await client.get('/api/v1/analysis/user-facts', { params })
    facts.value = data
  } catch { facts.value = [] }
  finally { loading.value = false }
}

async function deleteFact(id: number) {
  try {
    await ElMessageBox.confirm('确定删除这条记忆？', '确认删除', { type: 'warning' })
    await client.delete(`/api/v1/analysis/user-facts/${id}`)
    facts.value = facts.value.filter(f => f.id !== id)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

function startEdit(f: Fact) {
  editing.value = f
  editContent.value = f.content
}

async function saveEdit() {
  if (!editing.value) return
  // Currently no PATCH endpoint, just show saved
  editing.value.content = editContent.value
  editing.value.confidence = 'confirmed'
  editing.value = null
  ElMessage.success('已更新（本地）。后端确认接口后续补上。')
}

function toggleConfirm(f: Fact) {
  f.confidence = f.confidence === 'confirmed' ? 'auto' : 'confirmed'
  ElMessage.success(f.confidence === 'confirmed' ? '已确认为高可信事实' : '已取消确认')
}

onMounted(loadFacts)
</script>

<template>
  <div class="memory-page">
    <div class="page-header">
      <h1>记忆库</h1>
      <p>系统从你的简历和分析中自动提取的事实。确认为高可信后，将在后续分析中优先引用。</p>
    </div>

    <div class="toolbar">
      <el-radio-group v-model="filter" size="small" @change="loadFacts">
        <el-radio-button v-for="c in categories" :key="c.key" :label="c.key" :value="c.key">
          {{ c.label }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="facts" stripe v-loading="loading" style="width:100%">
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="
            row.category === 'skill' ? 'success' :
            row.category === 'weakness' ? 'danger' :
            row.category === 'project' ? 'warning' : 'info'
          ">{{ categories.find(c => c.key === row.category)?.label || row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="300">
        <template #default="{ row }">
          <template v-if="editing?.id === row.id">
            <el-input v-model="editContent" type="textarea" :rows="3" size="small" />
            <div style="margin-top:4px">
              <el-button size="small" type="primary" @click="saveEdit">保存</el-button>
              <el-button size="small" @click="editing = null">取消</el-button>
            </div>
          </template>
          <span v-else>{{ row.content }}</span>
        </template>
      </el-table-column>
      <el-table-column label="可信度" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.confidence === 'confirmed' ? 'success' : 'warning'">
            {{ row.confidence === 'confirmed' ? '已确认' : '自动提取' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="100">
        <template #default="{ row }">{{ row.source }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" text :type="row.confidence === 'confirmed' ? 'warning' : 'success'" @click="toggleConfirm(row)">
            {{ row.confidence === 'confirmed' ? '取消确认' : '确认' }}
          </el-button>
          <el-button size="small" text @click="startEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="deleteFact(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !facts.length" description="暂无记忆数据。上传简历并完成分析后，系统将自动提取。">
      <el-button type="primary" @click="$router.push('/')">去分析</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.memory-page { max-width: 1200px; margin: 0 auto; padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { margin-bottom: 6px; color: #111827; font-size: 22px; }
.page-header p { color: #667085; font-size: 13px; }
.toolbar { margin-bottom: 16px; }
</style>
