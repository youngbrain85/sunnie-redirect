export async function onRequestGet(context) {
  const { env } = context;
  
  try {
    // KV에서 모든 키 가져오기
    const listResult = await env.REDIRECTS.list();
    const keys = listResult.keys;
    
    // 메타데이터 가져오기
    const metadata = await env.REDIRECTS.get('_metadata');
    const metadataObj = metadata ? JSON.parse(metadata) : {};
    
    // 제품 목록 가져오기
    const products = {};
    
    // 각 키에 대한 값 가져오기
    for (const key of keys) {
      if (key.name !== '_metadata' && !key.name.startsWith('stats_')) {
        const value = await env.REDIRECTS.get(key.name);
        if (value) {
          products[key.name] = JSON.parse(value);
        }
      }
    }
    
    // 응답 데이터 구성
    const responseData = {
      products: products,
      metadata: metadataObj,
      count: Object.keys(products).length
    };
    
    return new Response(JSON.stringify(responseData), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    console.error('List error:', error);
    return new Response(JSON.stringify({ 
      error: 'Failed to fetch data',
      message: error.message 
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}

// OPTIONS 요청 처리 (CORS)
export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }
  });
}