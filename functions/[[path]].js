export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname.substring(1); // "/" 제거
  
  // 홈페이지 접근 시 대시보드로
  if (path === '' || path === '/') {
    return fetch(request);
  }
  
  try {
    // KV 스토리지에서 리다이렉션 데이터 가져오기
    const redirectData = await env.REDIRECTS.get(path);
    
    if (redirectData) {
      const data = JSON.parse(redirectData);
      
      // 통계 업데이트 (옵션)
      const stats = await env.REDIRECTS.get(`stats_${path}`) || '{"clicks":0}';
      const statsData = JSON.parse(stats);
      statsData.clicks++;
      statsData.lastClick = new Date().toISOString();
      await env.REDIRECTS.put(`stats_${path}`, JSON.stringify(statsData));
      
      // 301 영구 리다이렉션
      return Response.redirect(data.url, 301);
    }
    
    // 경로를 찾을 수 없는 경우 메인 추천인 링크로 리다이렉션 시도
    const mainData = await env.REDIRECTS.get('main');
    if (mainData) {
      const data = JSON.parse(mainData);
      return Response.redirect(data.url, 301);
    }
    
    // 404 페이지
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>페이지를 찾을 수 없습니다</title>
        <meta charset="utf-8">
        <style>
          body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px;
            background-color: #f5f5f5;
          }
          .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
          }
          h1 { color: #333; }
          p { color: #666; margin: 20px 0; }
          a { 
            color: #FF69B4; 
            text-decoration: none;
            font-weight: bold;
          }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>페이지를 찾을 수 없습니다</h1>
          <p>요청하신 제품 링크를 찾을 수 없습니다.</p>
          <p><a href="/">대시보드로 이동</a></p>
        </div>
      </body>
      </html>
    `, {
      status: 404,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
    
  } catch (error) {
    console.error('Redirect error:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
}