"""
NLP-based objective scoring for JD-resume matching.
Provides reference scores independent of LLM subjectivity.
"""
import re
import numpy as np
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class NLPScorer:
    """Compute objective match scores using NLP techniques."""

    def __init__(self):
        self._tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            token_pattern=r'(?u)\b\w+\b',
        )
        self._tech_keywords = self._load_tech_keywords()

    def score(self, resume_text: str, jd_text: str) -> dict:
        """Return multiple objective scores."""
        return {
            "tfidf_similarity": round(self._tfidf_score(resume_text, jd_text), 2),
            "keyword_coverage": round(self._keyword_score(resume_text, jd_text), 2),
            "skill_overlap": self._skill_overlap(resume_text, jd_text),
        }

    def _tfidf_score(self, resume: str, jd: str) -> float:
        """TF-IDF cosine similarity between JD and resume."""
        if len(resume.strip()) < 20 or len(jd.strip()) < 20:
            return 0.0
        try:
            matrix = self._tfidf.fit_transform([jd, resume])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(sim * 100)
        except Exception:
            return 0.0

    def _keyword_score(self, resume: str, jd: str) -> float:
        """What fraction of JD technical keywords appear in the resume?"""
        jd_keywords = set()
        for kw in self._tech_keywords:
            if kw.lower() in jd.lower():
                jd_keywords.add(kw.lower())

        if not jd_keywords:
            return 0.0

        found = sum(1 for kw in jd_keywords if kw.lower() in resume.lower())
        return found / len(jd_keywords) * 100

    def _skill_overlap(self, resume: str, jd: str) -> dict:
        """Which JD skills are found in the resume?"""
        jd_skills = set()
        resume_skills = set()
        for kw in self._tech_keywords:
            kl = kw.lower()
            if kl in jd.lower():
                jd_skills.add(kw)
            if kl in resume.lower():
                resume_skills.add(kw)

        matched = jd_skills & resume_skills
        missing = jd_skills - resume_skills
        return {
            "matched": sorted(matched)[:15],
            "missing": sorted(missing)[:15],
            "overlap_rate": round(len(matched) / len(jd_skills), 2) if jd_skills else 0,
        }

    @staticmethod
    def _load_tech_keywords() -> list[str]:
        """Extensive tech keyword list for matching."""
        return [
            # Languages
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C", "C++",
            "C#", "Scala", "Kotlin", "Swift", "Ruby", "PHP", "MATLAB", "R",
            "SQL", "Shell", "Bash",

            # AI/ML
            "PyTorch", "TensorFlow", "Keras", "scikit-learn", "XGBoost", "LightGBM",
            "Pandas", "NumPy", "SciPy", "Matplotlib", "Jupyter",
            "深度学习", "机器学习", "自然语言处理", "NLP", "计算机视觉", "CV",
            "Transformer", "BERT", "GPT", "LLM", "大模型", "RAG", "Agent",
            "LangChain", "LangGraph", "LlamaIndex", "向量数据库", "Fine-tuning",
            "RLHF", "Prompt Engineering", "模型部署", "模型压缩",

            # Backend
            "FastAPI", "Django", "Flask", "Spring", "Node.js", "Express",
            "Docker", "Kubernetes", "K8s", "微服务", "gRPC", "GraphQL",
            "RESTful", "API", "Redis", "RabbitMQ", "Kafka", "Nginx",
            "MySQL", "PostgreSQL", "MongoDB", "Elasticsearch", "SQLite",
            "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI",

            # Frontend
            "React", "Vue", "Angular", "Next.js", "Nuxt", "CSS", "HTML",
            "Webpack", "Vite", "WebAssembly",

            # DevOps
            "Linux", "AWS", "Azure", "GCP", "Terraform", "Ansible",
            "Prometheus", "Grafana", "ELK", "SRE",

            # Embedded / Hardware
            "MCU", "ARM", "STM32", "Arduino", "ESP32", "Raspberry Pi",
            "RTOS", "FreeRTOS", "嵌入式", "PCB", "SPI", "I2C", "传感器",

            # Tools
            "Git", "JIRA", "Confluence", "Figma", "Postman", "JMeter",

            # Domain
            "数据分析", "数据挖掘", "数据仓库", "ETL", "A/B测试",
            "Tableau", "PowerBI", "推荐系统", "搜索", "广告",
            "区块链", "智能合约", "Solidity", "DeFi", "Web3",
            "产品经理", "项目管理", "Scrum", "Agile",
        ]
