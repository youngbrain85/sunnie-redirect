#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 숫자 기반 ID를 영문 ID로 마이그레이션하는 스크립트
"""

import json
import re
import hashlib

def generate_product_id(product_name, existing_ids):
    """제품명 기반으로 고유한 영문 ID 생성"""
    
    # 한글을 영문으로 변환하기 위한 매핑
    korean_to_english_map = {
        '얼음': 'ice', '팩': 'pack', '지성': 'oily', '피부': 'skin',
        '건조': 'dry', '기미': 'melasma', '차단': 'block', '템': 'item',
        '스타터': 'starter', '쫀광': 'glow', '모공': 'pore', '스텝': 'step',
        '여드름': 'acne', '블블': 'blbl', '니기미': 'nigimi', '슈젝': 'suject',
        '세안': 'cleanse', '잡티': 'blemish', '장벽': 'barrier', '루티너': 'routine',
        '수면': 'sleep', '크림': 'cream', '물광': 'water', '완벽한': 'perfect',
        '파데프리': 'nobase', '어려보여': 'young', '그린': 'green', '잘': 'jal',
        '물먹': 'water', '화장': 'makeup', '필쥬란': 'pdrn', '파니쉬': 'finish',
        '제로': 'zero', '파데': 'base', '굿럭': 'goodluck', '건희': 'gunhee',
        '플루이노': 'fluino', '개': 'pcs', '님': '', '월': 'month',
        '파메위크': 'pharmweek', '메가실리엄': 'megacilium', '파메키': 'pharmkey',
        '프로모션': 'promo', '가정의': 'family', '달': 'day', '망각하는자': 'oblivion',
        '포마드': 'pomade', '파메스테틱': 'pharmesthetic', '키': 'key',
        '레빗밴드': 'rabbit', '파이널밤': 'finalbalm', '세멘잘라이트': 'cementlight',
        '세멘잘': 'cement', '그린박신': 'greenvax', '스트롱': 'strong',
        '로션폴리싱': 'lotionpolish', '겔스타터': 'gelstarter', '세멘스틱': 'cementstick',
        '겔폴리싱': 'gelpolish', '피니쉬로션': 'finishlotion', '튜토리얼키트': 'tutorial',
        '세멘시트': 'cementsheet', '가방': 'bag', '세멘팔트': 'cementphalt',
        '세멘잘라이트필름': 'cementfilm', '슈퍼젝션': 'superject', '픽시카': 'pixica',
        '파이토신': 'phytosin', '필름': 'film', '박스': 'box', '마호로사': 'mahorosa',
        '블루블러드': 'blueblood', '니기미봄므': 'nigimibomme'
    }
    
    # 제품명을 소문자로 변환하고 공백 제거
    cleaned_name = product_name.lower().strip()
    
    # 한글을 영문으로 변환
    for korean, english in korean_to_english_map.items():
        cleaned_name = cleaned_name.replace(korean, english)
    
    # 숫자와 특수문자 처리
    cleaned_name = re.sub(r'[^a-z0-9]+', '_', cleaned_name)
    cleaned_name = re.sub(r'_+', '_', cleaned_name).strip('_')
    
    # 빈 문자열이거나 너무 짧은 경우 해시 사용
    if len(cleaned_name) < 3:
        hash_suffix = hashlib.md5(product_name.encode()).hexdigest()[:6]
        cleaned_name = f"prod_{hash_suffix}"
    
    # 기본 ID 생성
    base_id = cleaned_name[:20]  # 최대 20자로 제한
    
    # 중복 확인 및 고유 ID 생성
    final_id = base_id
    counter = 1
    
    while final_id in existing_ids.values():
        # 이미 존재하는 ID인 경우 숫자 추가
        final_id = f"{base_id}_{counter}"
        counter += 1
    
    return final_id

def migrate_ids():
    """기존 ID 매핑을 영문 ID로 변환"""
    
    # 기존 매핑 파일 로드
    try:
        with open('product_id_mapping.json', 'r', encoding='utf-8') as f:
            old_mapping = json.load(f)
    except FileNotFoundError:
        print("기존 매핑 파일이 없습니다.")
        return
    
    # 백업 생성
    with open('product_id_mapping_backup.json', 'w', encoding='utf-8') as f:
        json.dump(old_mapping, f, ensure_ascii=False, indent=2)
    print("기존 매핑을 product_id_mapping_backup.json에 백업했습니다.")
    
    # 새 매핑 생성
    new_mapping = {}
    
    for product_name, old_id in old_mapping.items():
        new_id = generate_product_id(product_name, new_mapping)
        new_mapping[product_name] = new_id
        print(f"{product_name}: {old_id} -> {new_id}")
    
    # 새 매핑 저장
    with open('product_id_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(new_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n총 {len(new_mapping)}개의 제품 ID가 영문으로 변환되었습니다.")
    print("product_id_mapping.json 파일이 업데이트되었습니다.")

if __name__ == "__main__":
    migrate_ids()
