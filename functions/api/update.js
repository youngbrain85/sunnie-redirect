export async function onRequestPost(context) {
  const { request, env } = context;
  
  // API 키 검증
  const apiKey = request.headers.get('X-API-Key');
  if (apiKey !== env.API_KEY) {
    return new Response(JSON.stringify({ error: "인증 실패" }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  try {
    const data = await request.json();
    
    // 메타데이터 저장
    const metadata = {
      last_updated: Date.now(),
      last_updated_date: new Date().toISOString(),
      total_products: 0
    };
    
    // 각 리다이렉션 데이터 저장
    let count = 0;
    const updates = [];
    
    for (const [key, value] of Object.entries(data)) {
      if (key !== "_metadata") {
        // KV에 저장할 데이터 형식
        const kvData = {
          url: value.url || value,
          original_name: value.original_name || key,
          type: value.type || 'product',
          category: value.category || 'general',
          created_at: new Date().toISOString()
        };
        
        updates.push(env.REDIRECTS.put(key, JSON.stringify(kvData)));
        count++;
      }
    }
    
    // 모든 업데이트 병렬 처리
    await Promise.all(updates);
    
    // 메타데이터 업데이트
    metadata.total_products = count;
    await env.REDIRECTS.put('_metadata', JSON.stringify(metadata));
    
    // 제품 목록 저장 (대시보드용)
    const productList = Object.keys(data).filter(k => k !== '_metadata');
    await env.REDIRECTS.put('_product_list', JSON.stringify(productList));
    
    return new Response(JSON.stringify({ 
      success: true, 
      message: "업데이트 완료",
      count: count,
      timestamp: metadata.last_updated_date
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    console.error('Update error:', error);
    return new Response(JSON.stringify({ 
      error: error.message || "서버 오류가 발생했습니다" 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// OPTIONS 요청 처리 (CORS)
export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-API-Key',
    }
  });
}