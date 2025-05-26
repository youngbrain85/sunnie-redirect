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
    // 모든 키 가져오기
    let allKeys = [];
    let cursor = null;
    
    // 페이지네이션으로 모든 키 수집
    do {
      const listResult = await env.REDIRECTS.list({ cursor });
      allKeys = allKeys.concat(listResult.keys.map(key => key.name));
      cursor = listResult.cursor;
    } while (cursor);
    
    // 통계와 메타데이터는 유지하고 싶다면
    // const keysToDelete = allKeys.filter(key => !key.startsWith('stats_'));
    
    // 모든 키 삭제
    const deletePromises = allKeys.map(key => env.REDIRECTS.delete(key));
    await Promise.all(deletePromises);
    
    return new Response(JSON.stringify({ 
      success: true, 
      message: "모든 데이터가 초기화되었습니다",
      deleted: allKeys.length
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    console.error('Clear error:', error);
    return new Response(JSON.stringify({ 
      error: error.message || "초기화 중 오류가 발생했습니다" 
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