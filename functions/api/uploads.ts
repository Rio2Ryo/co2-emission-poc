// CSV アップロード処理
const uploads = new Map<string, any>();
const calculations = new Map<string, any>();

export async function onRequestPost(context) {
  const { request } = context;
  const formData = await request.formData();
  const file = formData.get('file') as File;
  const fileType = formData.get('fileType') as string;
  
  if (!file) {
    return new Response(JSON.stringify({ error: 'ファイルが必要です' }), { 
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  const text = await file.text();
  const lines = text.split('\n').filter(l => l.trim());
  const headers = lines[0].split(',').map(h => h.trim());
  const rows = lines.slice(1).map(l => {
    const values = l.split(',');
    const row: any = {};
    headers.forEach((h, i) => row[h] = values[i]?.trim() || '');
    return row;
  });

  const uploadId = `upload_${Date.now()}`;
  uploads.set(uploadId, {
    id: uploadId,
    filename: file.name,
    fileType,
    rowCount: rows.length,
    uploadedAt: new Date().toISOString(),
    status: 'processed',
    headers,
    sampleData: rows.slice(0, 3)
  });

  // 自動で算出実行
  const calcId = `calc_${Date.now()}`;
  const emissions = calculateEmissions(rows, fileType);
  calculations.set(calcId, {
    id: calcId,
    uploadId,
    createdAt: new Date().toISOString(),
    sourceType: fileType,
    grandTotalKg: emissions.total,
    scope1: emissions.scope1,
    scope2: emissions.scope2,
    scope3: emissions.scope3,
    status: 'completed',
    rowCount: rows.length
  });

  return new Response(JSON.stringify({
    uploadId,
    filename: file.name,
    rowCount: rows.length,
    status: 'processed',
    calcId,
    emissions: {
      total: emissions.total,
      scope1: emissions.scope1,
      scope2: emissions.scope2,
      scope3: emissions.scope3
    }
  }), {
    headers: { 
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

function calculateEmissions(rows: any[], fileType: string) {
  // 簡易排出係数（環境省 2023 年度版ベース）
  const factors: any = {
    accounting: {
      '電気代': { scope: 2, factor: 0.453, unit: 'kWh' },
      'ガソリン': { scope: 1, factor: 2.32, unit: 'L' },
      '軽油': { scope: 1, factor: 2.58, unit: 'L' },
      '都市ガス': { scope: 1, factor: 2.21, unit: 'm3' }
    },
    sales: {
      '製品': { scope: 3, factor: 0.5, unit: 'kg' }
    },
    pos: {
      'エコバッグ': { scope: 3, factor: 2.0, unit: '個' },
      '水筒': { scope: 3, factor: 1.5, unit: '個' },
      '箸セット': { scope: 3, factor: 0.1, unit: '個' }
    }
  };

  let scope1 = 0, scope2 = 0, scope3 = 0;
  const typeFactors = factors[fileType] || factors.accounting;

  rows.forEach(row => {
    const item = Object.values(row)[1] as string || '';
    const amount = parseFloat(Object.values(row)[2] as string) || 0;
    
    // 簡易マッチング
    let factor = 1.0;
    let scope = 3;
    
    for (const [key, f] of Object.entries(typeFactors)) {
      if (item.includes(key)) {
        factor = (f as any).factor;
        scope = (f as any).scope;
        break;
      }
    }

    const emission = amount * factor;
    if (scope === 1) scope1 += emission;
    else if (scope === 2) scope2 += emission;
    else scope3 += emission;
  });

  return { scope1, scope2, scope3, total: scope1 + scope2 + scope3 };
}

export async function onRequestGet(context) {
  const allUploads = Array.from(uploads.values());
  return new Response(JSON.stringify(allUploads), {
    headers: { 
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}

export async function onRequest(context) {
  if (context.request.method === 'POST') return onRequestPost(context);
  if (context.request.method === 'GET') return onRequestGet(context);
  return new Response('Method not allowed', { status: 405 });
}
