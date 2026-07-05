"""
Generate a large evaluation dataset for RAG retrieval testing.
Creates JDs across multiple domains using templates.
"""
import json
import random

random.seed(42)

DOMAINS = {
    "AI/大模型": {
        "companies": ["某AI公司", "某大模型初创", "某科技巨头AI Lab", "某NLP公司", "某Agent平台"],
        "positions": ["大模型应用开发工程师", "AI Agent开发工程师", "LLM算法工程师", "RAG系统工程师", "提示词工程师"],
        "skills": ["Python", "LangChain", "LangGraph", "RAG", "Prompt Engineering", "OpenAI API",
                   "向量数据库", "Agent", "MCP协议", "Function Calling", "DeepSeek", "Qwen",
                   "Fine-tuning", "RLHF", "Transformer", "Attention机制", "多模态"],
        "keywords": ["大模型", "Agent", "RAG检索增强", "MCP", "LangGraph工作流", "多智能体",
                     "知识库", "文档解析", "语义检索", "工具调用", "自主决策"],
    },
    "后端开发": {
        "companies": ["某电商平台", "某金融科技", "某SaaS公司", "某游戏公司", "某物流平台"],
        "positions": ["Python后端工程师", "Go开发工程师", "Java后端开发", "Node.js工程师", "后端架构师"],
        "skills": ["Python", "Go", "Java", "Django", "FastAPI", "Spring Boot", "MySQL", "PostgreSQL",
                   "Redis", "Docker", "Kubernetes", "gRPC", "消息队列", "微服务", "RESTful API"],
        "keywords": ["后端服务", "API设计", "数据库优化", "高并发", "分布式系统", "缓存策略",
                     "容器化部署", "CI/CD", "性能调优", "数据一致性"],
    },
    "前端开发": {
        "companies": ["某互联网公司", "某在线教育", "某社交平台", "某工具产品", "某内容平台"],
        "positions": ["前端开发工程师", "React工程师", "Vue前端开发", "全栈工程师", "Web前端架构师"],
        "skills": ["JavaScript", "TypeScript", "React", "Vue3", "CSS", "HTML", "Webpack", "Vite",
                   "Node.js", "SSR", "小程序开发", "跨平台", "WebAssembly"],
        "keywords": ["前端框架", "组件库", "状态管理", "响应式布局", "性能优化", "SEO",
                     "前后端分离", "SSR渲染", "微前端"],
    },
    "嵌入式/硬件": {
        "companies": ["某智能硬件公司", "某机器人公司", "某IoT平台", "某芯片公司", "某可穿戴设备"],
        "positions": ["嵌入式软件工程师", "硬件工程师", "MCU开发工程师", "IoT开发工程师", "驱动开发工程师"],
        "skills": ["C", "C++", "ARM", "MCU", "STM32", "Arduino", "ESP32", "RTOS",
                   "电路设计", "PCB", "SPI", "I2C", "UART", "传感器", "FreeRTOS"],
        "keywords": ["嵌入式", "单片机", "硬件调试", "传感器", "GPIO", "PWM", "ADC",
                     "示波器", "焊接", "低功耗", "实时系统"],
    },
    "DevOps/运维": {
        "companies": ["某云计算公司", "某SaaS平台", "某银行科技", "某直播平台", "某安全公司"],
        "positions": ["DevOps工程师", "SRE工程师", "云平台运维", "安全运维工程师", "基础设施工程师"],
        "skills": ["Linux", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
                   "Prometheus", "Grafana", "ELK", "AWS", "Azure", "Shell", "Python"],
        "keywords": ["运维自动化", "容器编排", "监控告警", "日志分析", "故障排查",
                     "容量规划", "安全加固", "网络配置", "负载均衡"],
    },
    "数据分析": {
        "companies": ["某电商数据部", "某金融风控", "某咨询公司", "某互联网增长团队", "某广告平台"],
        "positions": ["数据分析师", "BI工程师", "数据运营", "商业分析师", "增长分析师"],
        "skills": ["SQL", "Python", "Pandas", "Excel", "Tableau", "PowerBI",
                   "统计学", "A/B测试", "数据可视化", "ETL", "数据仓库"],
        "keywords": ["数据分析", "报表开发", "用户画像", "指标拆解", "归因分析",
                     "漏斗分析", "留存分析", "数据看板"],
    },
    "算法/机器学习": {
        "companies": ["某推荐系统公司", "某自动驾驶", "某搜索平台", "某广告算法", "某量化基金"],
        "positions": ["算法工程师", "机器学习工程师", "推荐算法工程师", "NLP算法工程师", "CV算法工程师"],
        "skills": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Spark", "特征工程",
                   "深度学习", "XGBoost", "模型部署", "A/B实验", "数据挖掘"],
        "keywords": ["推荐系统", "排序模型", "CTR预估", "NLP", "图像识别", "目标检测",
                     "模型压缩", "知识蒸馏", "在线学习"],
    },
    "测试/QA": {
        "companies": ["某互联网质量部", "某金融测试中心", "某游戏QA", "某移动应用", "某企业软件"],
        "positions": ["测试工程师", "自动化测试工程师", "性能测试工程师", "测试开发", "质量保证工程师"],
        "skills": ["Python", "Selenium", "JMeter", "Postman", "Jenkins", "Git",
                   "测试用例设计", "自动化框架", "性能测试", "接口测试", "Appium"],
        "keywords": ["测试策略", "回归测试", "黑盒白盒", "CI/CD集成", "缺陷管理", "测试报告"],
    },
    "产品/项目": {
        "companies": ["某互联网产品部", "某SaaS创业", "某电商平台", "某教育科技", "某医疗IT"],
        "positions": ["产品经理", "项目主管", "技术项目经理", "产品运营", "解决方案架构师"],
        "skills": ["需求分析", "PRD撰写", "竞品分析", "Axure", "JIRA", "数据分析",
                   "用户研究", "敏捷开发", "Scrum", "跨部门协作"],
        "keywords": ["需求管理", "产品规划", "迭代排期", "用户访谈", "数据驱动",
                     "路线图", "MVP", "增长黑客"],
    },
    "区块链/Web3": {
        "companies": ["某Web3创业", "某DeFi平台", "某NFT市场", "某公链项目", "某交易所"],
        "positions": ["区块链开发工程师", "智能合约工程师", "Web3前端", "DeFi协议开发", "区块链架构师"],
        "skills": ["Solidity", "Rust", "Go", "Ethereum", "Web3.js", "智能合约",
                   "共识算法", "P2P网络", "密码学", "DeFi", "NFT"],
        "keywords": ["区块链", "去中心化", "智能合约审计", "EVM", "Layer2",
                     "跨链", "钱包", "DApp"],
    },
}


def generate_jd(domain_name: str, domain: dict, idx: int) -> dict:
    company = random.choice(domain["companies"])
    position = random.choice(domain["positions"])
    skills = random.sample(domain["skills"], min(5 + random.randint(1, 4), len(domain["skills"])))
    keywords = random.sample(domain["keywords"], min(3, len(domain["keywords"])))
    text = f"{company}招聘{position}。要求：{'、'.join(skills)}。{'、'.join(keywords)}。"
    return {
        "company": company, "position": position, "jd_text": text,
        "skills": ",".join(skills), "match_score": random.randint(20, 90),
        "domain": domain_name, "id": idx,
    }


def generate_queries(domain_name: str, domain: dict, count: int) -> list[str]:
    queries = []
    skills = domain["skills"]
    positions = domain["positions"]
    for _ in range(count):
        s = random.sample(skills, min(2, len(skills)))
        q = f"{' '.join(s)} {random.choice(positions).split('工程师')[0]}"
        queries.append(q)
    return queries


def main(num_jds: int = 500):
    jds = []
    evals = []
    # Distribute across domains
    domains_list = list(DOMAINS.items())
    jds_per_domain = max(1, num_jds // len(domains_list))

    idx = 0
    for domain_name, domain in domains_list:
        for i in range(jds_per_domain):
            jd = generate_jd(domain_name, domain, idx)
            jds.append(jd)
            idx += 1

    # Pad remaining
    while len(jds) < num_jds:
        domain_name, domain = random.choice(domains_list)
        jd = generate_jd(domain_name, domain, idx)
        jds.append(jd)
        idx += 1

    # Generate eval cases: for each domain, the query should match JDs in that domain
    for domain_name, domain in domains_list:
        domain_jd_ids = [j["id"] for j in jds if j["domain"] == domain_name][:10]
        queries = generate_queries(domain_name, domain, 2)
        for q in queries:
            evals.append({"query": q, "expected_domain": domain_name, "expected_ids": domain_jd_ids})

    random.shuffle(evals)

    # Save
    with open("evals/datasets/eval_set_500.json", "w", encoding="utf-8") as f:
        json.dump({"jds": jds, "evals": evals[:50]}, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(jds)} JDs across {len(domains_list)} domains")
    print(f"Generated {len(evals[:50])} eval queries")
    domains_set = set(j["domain"] for j in jds)
    for d in sorted(domains_set):
        count = sum(1 for j in jds if j["domain"] == d)
        print(f"  {d}: {count}")


if __name__ == "__main__":
    main()
