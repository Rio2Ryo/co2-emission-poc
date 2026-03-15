const uploads = new Map<string, any>();
const calculations = new Map<string, any>();

// 初期テストデータ
calculations.set('calc_001', { id: 'calc_001', createdAt: '2024-03-01T10:00:00Z', sourceType: 'accounting', grandTotalKg: 1245.5, scope1: 563.5, scope2: 482, scope3: 200, status: 'completed', rowCount: 8 });
calculations.set('calc_002', { id: 'calc_002', createdAt: '2024-03-05T14:30:00Z', sourceType: 'sales', grandTotalKg: 856, scope1: 325.5, scope2: 330.5, scope3: 200, status: 'completed', rowCount: 6 });
calculations.set('calc_003', { id: 'calc_003', createdAt: '2024-03-10T09:15:00Z', sourceType: 'pos', grandTotalKg: 746, scope1: 356, scope2: 290, scope3: 100, status: 'completed', rowCount: 5 });
uploads.set('upload_001', { id: 'upload_001', filename: 'accounting_test.csv', uploadedAt: '2024-03-01T09:00:00Z', rowCount: 8, status: 'processed' });
uploads.set('upload_002', { id: 'upload_002', filename: 'sales_test.csv', uploadedAt: '2024-03-05T14:00:00Z', rowCount: 6, status: 'processed' });
uploads.set('upload_003', { id: 'upload_003', filename: 'pos_test.csv', uploadedAt: '2024-03-10T08:30:00Z', rowCount: 5, status: 'processed' });

const corsHeaders = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  
  if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

  // Health
  if (url.pathname === '/api/health' || url.pathname === '/health') {
    return new Response(JSON.stringify({ status: 'ok', version: '0.1.0', timestamp: new Date().toISOString() }), { headers: corsHeaders });
  }

  // Dashboard Summary
  if (url.pathname === '/api/dashboard/summary' || url.pathname === '/api/v1/dashboard/summary') {
    const calcs = Array.from(calculations.values());
    const total = calcs.reduce((s, c) => s + c.grandTotalKg, 0);
    const s1 = calcs.reduce((s, c) => s + c.scope1, 0);
    const s2 = calcs.reduce((s, c) => s + c.scope2, 0);
    const s3 = calcs.reduce((s, c) => s + c.scope3, 0);
    return new Response(JSON.stringify({ total_calculations: calcs.length, total_emissions_kg: total, scope1_kg: s1, scope2_kg: s2, scope3_kg: s3, last_updated: new Date().toISOString(), trend: 'increasing' }), { headers: corsHeaders });
  }

  // Calculations
  if (url.pathname === '/api/calculations' || url.pathname === '/api/v1/calculations') {
    return new Response(JSON.stringify(Array.from(calculations.values())), { headers: corsHeaders });
  }

  // Uploads
  if (url.pathname === '/api/uploads' || url.pathname === '/api/v1/uploads') {
    if (request.method === 'POST') {
      const formData = await request.formData();
      const file = formData.get('file') as File;
      const fileType = formData.get('fileType') as string || 'accounting';
      if (!file) return new Response(JSON.stringify({ error: 'ファイルが必要です' }), { status: 400, headers: corsHeaders });
      
      const text = await file.text();
      const lines = text.split('\n').filter(l => l.trim());
      const rows = lines.slice(1);
      const uploadId = `upload_${Date.now()}`;
      uploads.set(uploadId, { id: uploadId, filename: file.name, uploadedAt: new Date().toISOString(), rowCount: rows.length, status: 'processed', fileType });
      
      // 自動算出
      const emissions = calcEmissions(rows, fileType);
      const calcId = `calc_${Date.now()}`;
      calculations.set(calcId, { id: calcId, uploadId, createdAt: new Date().toISOString(), sourceType: fileType, grandTotalKg: emissions.total, scope1: emissions.scope1, scope2: emissions.scope2, scope3: emissions.scope3, status: 'completed', rowCount: rows.length });
      
      return new Response(JSON.stringify({ uploadId, filename: file.name, rowCount: rows.length, status: 'processed', calcId, emissions }), { headers: corsHeaders });
    }
    return new Response(JSON.stringify(Array.from(uploads.values())), { headers: corsHeaders });
  }

  return new Response(JSON.stringify({ message: 'CO2 Emission API', endpoints: ['/health', '/api/dashboard/summary', '/api/v1/calculations', '/api/v1/uploads'] }), { headers: corsHeaders });
}

function calcEmissions(rows: string[], fileType: string) {
  const factors: any = {
    accounting: { '電気': { s: 2, f: 0.453 }, 'ガソリン': { s: 1, f: 2.32 }, '軽油': { s: 1, f: 2.58 }, 'ガス': { s: 1, f: 2.21 } },
    sales: { '製品': { s: 3, f: 0.5 } },
    pos: { 'エコ': { s: 3, f: 2.0 }, '水筒': { s: 3, f: 1.5 }, '箸': { s: 3, f: 0.1 } }
  };
  const f = factors[fileType] || factors.accounting;
  let s1 = 0, s2 = 0, s3 = 0;
  rows.forEach(r => {
    const cols = r.split(',');
    const item = cols[1] || '';
    const amt = parseFloat(cols[2]) || 0;
    let factor = 1, scope = 3;
    for (const [k, v] of Object.entries(f)) { if (item.includes(k)) { factor = (v as any).f; scope = (v as any).s; break; } }
    const e = amt * factor;
    if (scope === 1) s1 += e; else if (scope === 2) s2 += e; else s3 += e;
  });
  return { scope1: s1, scope2: s2, scope3: s3, total: s1 + s2 + s3 };
}
