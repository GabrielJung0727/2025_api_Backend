"""
딥시크 AI 기반 난이도 및 유형 자동 분석 서비스
평가위원 6명의 난이도 패턴을 평균화하여 AI 학습 후 자동 예측
"""
import json
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

import requests
from sqlalchemy.orm import Session

from ..models.question import Question
from ..core.config import settings

logger = logging.getLogger(__name__)

class DifficultyAnalyzer:
    """AI 기반 난이도 분석기"""
    
    def __init__(self):
        self.evaluation_data_path = "app/data/detailed_evaluator_analysis.json"
        self.learning_patterns = {}
        self.ollama_url = "http://localhost:11434/api/generate"  # Ollama API
        
        # 평가위원 난이도 패턴 로드
        self.load_evaluator_patterns()
        
        # 평균화된 난이도 패턴 생성
        self.generate_averaged_patterns()
    
    def load_evaluator_patterns(self):
        """평가위원별 난이도 패턴 로드"""
        try:
            if os.path.exists(self.evaluation_data_path):
                with open(self.evaluation_data_path, 'r', encoding='utf-8') as f:
                    self.evaluation_data = json.load(f)
                    logger.info("✅ 평가위원 난이도 패턴 로드 완료")
            else:
                logger.warning("❌ 평가위원 데이터 파일이 없습니다")
                self.evaluation_data = {}
        except Exception as e:
            logger.error(f"❌ 평가위원 데이터 로드 실패: {e}")
            self.evaluation_data = {}
    
    def generate_averaged_patterns(self):
        """6명 평가위원의 난이도 패턴 평균화"""
        self.learning_patterns = {
            "물리치료": {
                "question_difficulty_map": {},  # 문제번호별 평균 난이도
                "difficulty_distribution": {},  # 전체 난이도 분포
                "subject_patterns": {},         # 과목별 난이도 패턴
                "year_trends": {}              # 년도별 트렌드
            },
            "작업치료": {
                "question_difficulty_map": {},
                "difficulty_distribution": {},
                "subject_patterns": {},
                "year_trends": {}
            }
        }
        
        for dept, dept_data in self.evaluation_data.get("departments", {}).items():
            self.analyze_department_patterns(dept, dept_data)
        
        logger.info("✅ 평가위원 패턴 평균화 완료")
    
    def analyze_department_patterns(self, dept: str, dept_data: dict):
        """학과별 평가위원 패턴 분석"""
        evaluators = dept_data.get("evaluators", {})
        
        # 문제번호별 난이도 수집 (1-22번)
        question_difficulties = defaultdict(list)  # {문제번호: [난이도1, 난이도2, ...]}
        all_difficulties = []
        
        for evaluator_name, eval_data in evaluators.items():
            for year, year_detail in eval_data.get("years_detail", {}).items():
                difficulty_by_question = year_detail.get("difficulty_by_question", {})
                
                for q_num, difficulty in difficulty_by_question.items():
                    if q_num.isdigit() and int(q_num) <= 22:  # 1-22번 문제만
                        question_difficulties[int(q_num)].append(difficulty)
                        all_difficulties.append(difficulty)
        
        # 문제번호별 평균 난이도 계산
        question_avg_difficulty = {}
        for q_num in range(1, 23):  # 1-22번
            if q_num in question_difficulties:
                difficulties = question_difficulties[q_num]
                # 가장 많이 나온 난이도를 평균으로 사용
                avg_difficulty = Counter(difficulties).most_common(1)[0][0]
                question_avg_difficulty[q_num] = avg_difficulty
        
        # 전체 난이도 분포
        difficulty_distribution = Counter(all_difficulties)
        
        # 학습 패턴 저장
        self.learning_patterns[dept]["question_difficulty_map"] = question_avg_difficulty
        self.learning_patterns[dept]["difficulty_distribution"] = dict(difficulty_distribution)
        
        logger.info(f"📊 {dept}학과 패턴 분석 완료: {len(question_avg_difficulty)}개 문제 매핑")
    
    def predict_difficulty_by_position(self, question_number: int, department: str) -> str:
        """문제 번호 기반 난이도 예측"""
        dept_patterns = self.learning_patterns.get(department, {})
        question_map = dept_patterns.get("question_difficulty_map", {})
        
        # 해당 문제 번호의 평균 난이도 반환
        if question_number in question_map:
            return question_map[question_number]
        
        # 없으면 분포 기반 예측
        difficulty_dist = dept_patterns.get("difficulty_distribution", {})
        if difficulty_dist:
            # 가장 많이 나온 난이도를 기본값으로
            return max(difficulty_dist.items(), key=lambda x: x[1])[0]
        
        return "중"  # 기본값
    
    def analyze_with_deepseek(self, question_content: str, department: str) -> Dict[str, str]:
        """딥시크 AI를 통한 문제 내용 기반 난이도, 유형 및 영역이름 분석"""
        try:
            # 학과별 학습 패턴 정보
            dept_patterns = self.learning_patterns.get(department, {})
            difficulty_dist = dept_patterns.get("difficulty_distribution", {})
            
            # 프롬프트 생성
            prompt = self.create_analysis_prompt(question_content, department, difficulty_dist)
            
            # Ollama 딥시크 호출
            response = self.call_ollama_deepseek(prompt)
            
            if response:
                return self.parse_analysis_response(response, department)
            else:
                return self.get_fallback_analysis(department)
                
        except Exception as e:
            logger.error(f"❌ 딥시크 분석 실패: {e}")
            return self.get_fallback_analysis(department)
    
    def create_analysis_prompt(self, question_content: str, department: str, difficulty_dist: dict) -> str:
        """딥시크 분석용 프롬프트 생성 - 영역이름까지 분석"""
        # 학과별 특성화된 프롬프트
        dept_context = {
            "물리치료": "물리치료사 국가고시 문제로, 해부학, 생리학, 운동치료학, 물리치료진단학 등의 영역",
            "작업치료": "작업치료사 국가고시 문제로, 해부학, 생리학, 작업치료학, 인지재활학 등의 영역"
        }
        
        context = dept_context.get(department, "보건의료 관련 국가고시 문제")
        
        # 평가위원 난이도 분포 정보
        dist_info = ""
        if difficulty_dist:
            total = sum(difficulty_dist.values())
            percentages = {k: f"{(v/total*100):.1f}%" for k, v in difficulty_dist.items()}
            dist_info = f"기존 평가위원 6명의 난이도 분포: {percentages}"
        
        # 평가위원 데이터에서 가능한 영역이름 목록 가져오기
        area_names = self._get_available_area_names(department)
        area_list = ", ".join(area_names[:10])  # 처음 10개만 표시
        if len(area_names) > 10:
            area_list += f" 등 {len(area_names)}개"
        
        prompt = f"""
당신은 {department}학과 전문가입니다. 다음 문제의 난이도, 유형, 영역을 분석해주세요.

**분석 대상 문제:**
{question_content}

**문제 특성:**
- {context}
- 22문제 중 하나로 구성
- {dist_info}

**분석 요청:**
1. 난이도: "하", "중", "상" 중 하나
2. 문제유형: "객관식", "단답형", "서술형", "계산형", "임상형" 중 하나
3. 영역이름: 다음 중 가장 적절한 것 선택
   - 사용 가능한 영역: {area_list}

**분석 기준:**
- 하: 기본 개념, 단순 암기 문제
- 중: 응용 이해, 연관성 파악 문제  
- 상: 종합 분석, 임상 적용 문제

**응답 형식 (JSON):**
{{
  "difficulty": "중",
  "question_type": "객관식",
  "area_name": "신경계통",
  "reasoning": "분석 근거"
}}
"""
        return prompt
    
    def _get_available_area_names(self, department: str) -> list:
        """평가위원 데이터에서 사용 가능한 영역이름 목록 조회"""
        try:
            from .evaluator_type_mapper import evaluator_type_mapper
            dept_name = department + "학과"
            return evaluator_type_mapper.get_available_types(dept_name)
        except Exception as e:
            logger.warning(f"⚠️ 영역이름 목록 조회 실패: {e}")
            # 기본 영역이름 반환
            if department == "물리치료":
                return ["인체의 구분과 조직", "뼈대계통", "관절계통", "근육계통", "순환계통", "호흡계통", "소화계통", "비뇨계통 및 내분비계통", "신경계통", "피부계통 및 특수감각계통"]
            elif department == "작업치료":
                return ["인체의 체계", "뼈대와 관절계(통)", "근육계(통)", "신경계(통)", "심혈관계(통), 면역계(통)", "호흡, 음성, 말하기 기능", "신경계(통)의 기능", "근육계(통)의 기능"]
            else:
                return ["일반"]
    
    def call_ollama_deepseek(self, prompt: str) -> Optional[str]:
        """Ollama를 통한 딥시크 호출"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # 시스템 프롬프트와 사용자 프롬프트 합치기 (영어로 간단하게)
            full_prompt = f"""You are a medical exam analysis expert. Analyze this Korean medical question and return JSON format.

Question: {prompt[:500]}...

Return JSON with: {{"difficulty": "하/중/상", "question_type": "객관식", "reasoning": "brief analysis"}}"""
            
            data = {
                "model": "deepseek-r1:8b",
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                self.ollama_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.warning(f"⚠️ Ollama 연결 실패: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ Ollama가 실행되지 않음. 패턴 기반 분석으로 대체")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Ollama 호출 실패: {e}")
            return None
    
    def parse_analysis_response(self, response: str, department: str = "물리치료") -> Dict[str, str]:
        """딥시크 응답 파싱 - 영역이름 포함"""
        try:
            # JSON 추출 시도
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                difficulty = analysis.get("difficulty", "중")
                question_type = analysis.get("question_type", "객관식")
                area_name = analysis.get("area_name", "")
                reasoning = analysis.get("reasoning", "AI 분석 결과")
                
                # 유효성 검증
                valid_difficulties = ["하", "중", "상"]
                valid_types = ["객관식", "단답형", "서술형", "계산형", "임상형"]
                
                if difficulty not in valid_difficulties:
                    difficulty = "중"
                if question_type not in valid_types:
                    question_type = "객관식"
                
                # 영역이름 유효성 검증
                valid_areas = self._get_available_area_names(department)
                if area_name not in valid_areas:
                    # 가장 일반적인 영역으로 폴백
                    area_name = valid_areas[0] if valid_areas else "일반"
                
                return {
                    "difficulty": difficulty,
                    "question_type": question_type,
                    "area_name": area_name,
                    "ai_reasoning": reasoning
                }
            
        except Exception as e:
            logger.error(f"❌ 응답 파싱 실패: {e}")
        
        # 파싱 실패시 기본값
        return {
            "difficulty": "중",
            "question_type": "객관식",
            "area_name": self._get_default_area_name(department),
            "ai_reasoning": "AI 분석 중 오류 발생"
        }
    
    def _get_default_area_name(self, department: str) -> str:
        """학과별 기본 영역이름"""
        if department == "물리치료":
            return "인체의 구분과 조직"
        elif department == "작업치료":
            return "인체의 체계"
        else:
            return "일반"
    
    def get_fallback_analysis(self, department: str) -> Dict[str, str]:
        """로컬 딥시크 분석 실패시 대체 분석"""
        # 평가위원 패턴 기반 기본값
        dept_patterns = self.learning_patterns.get(department, {})
        difficulty_dist = dept_patterns.get("difficulty_distribution", {})
        
        # 가장 많이 나온 난이도를 기본값으로
        default_difficulty = "중"
        if difficulty_dist:
            default_difficulty = max(difficulty_dist.items(), key=lambda x: x[1])[0]
        
        return {
            "difficulty": default_difficulty,
            "question_type": "객관식",
            "area_name": self._get_default_area_name(department),
            "ai_reasoning": "평가위원 6명 패턴 기반 분석 (Ollama 미실행)"
        }
    
    def analyze_question_auto(self, question_content: str, question_number: int, department: str) -> Dict[str, str]:
        """자동 문제 분석 (번호 기반 + AI 내용 분석 조합) - 영역이름 포함"""
        logger.info(f"🤖 AI 난이도 및 영역 분석 시작: {department}학과 {question_number}번 문제")
        
        # 1. 문제 번호 기반 예측
        position_difficulty = self.predict_difficulty_by_position(question_number, department)
        
        # 2. 딥시크 AI 내용 분석 (난이도, 유형, 영역이름)
        ai_analysis = self.analyze_with_deepseek(question_content, department)
        
        # 3. 결과 조합 
        final_difficulty = ai_analysis.get("difficulty", position_difficulty)
        question_type = ai_analysis.get("question_type", "객관식")
        area_name = ai_analysis.get("area_name", self._get_default_area_name(department))
        ai_reasoning = ai_analysis.get("ai_reasoning", "자동 분석 완료")
        
        result = {
            "difficulty": final_difficulty,
            "question_type": question_type,
            "area_name": area_name,
            "ai_reasoning": ai_reasoning,
            "position_based": position_difficulty,
            "ai_suggested": ai_analysis.get("difficulty", "중"),
            "confidence": "high" if final_difficulty == position_difficulty else "medium"
        }
        
        logger.info(f"✅ AI 분석 완료: 난이도={final_difficulty}, 유형={question_type}, 영역={area_name}")
        return result
    
    def get_learning_summary(self) -> Dict:
        """학습된 패턴 요약 정보"""
        summary = {
            "total_patterns": len(self.learning_patterns),
            "departments": {}
        }
        
        for dept, patterns in self.learning_patterns.items():
            dept_summary = {
                "question_mappings": len(patterns.get("question_difficulty_map", {})),
                "difficulty_distribution": patterns.get("difficulty_distribution", {}),
                "total_evaluators": 6,
                "pattern_confidence": "high"
            }
            summary["departments"][dept] = dept_summary
        
        return summary

# 전역 인스턴스
difficulty_analyzer = DifficultyAnalyzer() 