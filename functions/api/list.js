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
    
    // 메타데이터에서 오늘 제품 목록 가져오기
    const todayProducts = metadataObj.today_products || [];
    
    // 오늘 제품만 가져오기
    if (todayProducts.length > 0) {
      // 오늘 제품 목록이 있으면 해당 제품만
      for (const productId of todayProducts) {
        // 내부 메타데이터는 제외
        if (productId.startsWith('_')) continue;
        
        const value = await env.REDIRECTS.get(productId);
        if (value) {
          products[productId] = JSON.parse(value);
        }
      }
    } else {
      // 오늘 제품 목록이 없으면 모든 제품 (기존 방식)
      for (const key of keys) {
        if (key.name !== '_metadata' && 
            !key.name.startsWith('stats_') && 
            !key.name.startsWith('_')) {  // 언더스코어로 시작하는 내부 키 제외
          const value = await env.REDIRECTS.get(key.name);
          if (value) {
            products[key.name] = JSON.parse(value);
          }
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