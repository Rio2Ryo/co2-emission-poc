const uploads = new Map<string, any>();
const calculations = new Map<string, any>();
const emissionFactors = new Map<string, any>();

// Initial test data
calculations.set('calc_001', { id: 'calc_001', createdAt: '2024-03-01T10:00:00Z', sourceType: 'accounting', grandTotalKg: 1245.5, scope1: 563.5, scope2: 482, scope3: 200, status: 'completed', rowCount: 8 });
calculations.set('calc_002', { id: 'calc_002', createdAt: '2024-03-05T14:30:00Z', sourceType: 'sales', grandTotalKg: 856, scope1: 325.5, scope2: 330.5, scope3: 200, status: 'completed', rowCount: 6 });
calculations.set('calc_003', { id: 'calc_003', createdAt: '2024-03-10T09:15:00Z', sourceType: 'pos', grandTotalKg: 746, scope1: 356, scope2: 290, scope3: 100, status: 'completed', rowCount: 5 });
uploads.set('upload_001', { id: 'upload_001', filename: 'accounting_test.csv', uploadedAt: '2024-03-01T09:00:00Z', rowCount: 8, status: 'processed' });
uploads.set('upload_002', { id: 'upload_002', filename: 'sales_test.csv', uploadedAt: '2024-03-05T14:00:00Z', rowCount: 6, status: 'processed' });
uploads.set('upload_003', { id: 'upload_003', filename: 'pos_test.csv', uploadedAt: '2024-03-10T08:30:00Z', rowCount: 5, status: 'processed' });

// Emission Factors DB
const initialFactors = [
  { id: 'ef_jp_001', name: '電気（日本）', source: '環境省 2023', scope: 2, factor: 0.453, unit: 'kWh', country: 'JP', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_002', name: 'ガソリン', source: '環境省 2023', scope: 1, factor: 2.32, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_003', name: '軽油', source: '環境省 2023', scope: 1, factor: 2.58, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_004', name: '都市ガス', source: '環境省 2023', scope: 1, factor: 2.21, unit: 'm3', country: 'JP', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_us_001', name: 'Electricity (US)', source: 'EPA 2023', scope: 2, factor: 0.386, unit: 'kWh', country: 'US', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_us_002', name: 'Gasoline (US)', source: 'EPA 2023', scope: 1, factor: 2.31, unit: 'L', country: 'US', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_iea_001', name: 'Natural Gas', source: 'IEA 2023', scope: 1, factor: 2.0, unit: 'm3', country: 'INTL', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_005', name: '製品 A（標準）', source: 'IDEA 2023', scope: 3, factor: 0.5, unit: 'kg', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_006', name: 'エコバッグ', source: 'IDEA 2023', scope: 3, factor: 2.0, unit: '個', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31' },
  { id: 'ef_jp_007', name: '水筒', source: 'IDEA 2023', scope: 3, factor: 1.5, unit: '個', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31' }
];
initialFactors.forEach(f => emissionFactors.set(f.id, f));

const corsHeaders = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  
  if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

  // Health
  if (url.pathname === '/api/health' || url.pathname === '/health') {
    return new Response(JSON.stringify({ status: 'ok', version: '1.0.0-mvp', timestamp: new Date().toISOString() }), { headers: corsHeaders });
  }

  // Dashboard Summary
  if (url.pathname === '/api/dashboard/summary' || url.pathname === '/api/v1/dashboard/summary') {
    const calcs = Array.from(calculations.values());
    const total = calcs.reduce((s, c) => s + (c.grandTotalKg || c.grand_total_kg || 0), 0);
    const s1 = calcs.reduce((s, c) => s + (c.scope1 || 0), 0);
    const s2 = calcs.reduce((s, c) => s + (c.scope2 || 0), 0);
    const s3 = calcs.reduce((s, c) => s + (c.scope3 || 0), 0);
    return new Response(JSON.stringify({ total_calculations: calcs.length, total_emissions_kg: total, scope1_kg: s1, scope2_kg: s2, scope3_kg: s3, last_updated: new Date().toISOString(), trend: 'increasing' }), { headers: corsHeaders });
  }

  // Calculations
  if (url.pathname === '/api/calculations' || url.pathname === '/api/v1/calculations') {
    return new Response(JSON.stringify(Array.from(calculations.values())), { headers: corsHeaders });
  }

  // Calculation Detail with Breakdown
  if (url.pathname.match(/^\/api\/calculations\/[^\/]+$/)) {
    const calcId = url.pathname.split('/').pop();
    const calc = calculations.get(calcId);
    if (!calc) return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: corsHeaders });
    return new Response(JSON.stringify(calc), { headers: corsHeaders });
  }

  // Uploads
  if (url.pathname === '/api/uploads' || url.pathname === '/api/v1/uploads') {
    if (request.method === 'POST') {
      const contentType = request.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const body = await request.json();
        const emissions = calcWithMapping(body.rows || [], body.mapping || {}, body.fileType || 'accounting');
        const breakdown = createBreakdown(body.rows || [], body.mapping || {}, body.fileType || 'accounting');
        const calcId = `calc_${Date.now()}`;
        calculations.set(calcId, { id: calcId, uploadId: body.uploadId, createdAt: new Date().toISOString(), sourceType: body.fileType, grandTotalKg: emissions.total, scope1: emissions.scope1, scope2: emissions.scope2, scope3: emissions.scope3, status: 'completed', rowCount: (body.rows || []).length, mapping: body.mapping, breakdown });
        return new Response(JSON.stringify({ calcId, emissions, breakdown }), { headers: corsHeaders });
      }
      const formData = await request.formData();
      const file = formData.get('file') as File;
      const fileType = formData.get('fileType') as string || 'accounting';
      const preview = formData.get('preview') === 'true';
      if (!file) return new Response(JSON.stringify({ error: 'ファイルが必要です' }), { status: 400, headers: corsHeaders });
      const text = await file.text();
      const lines = text.split('\n').filter(l => l.trim());
      const headers = lines[0].split(',').map(h => h.trim());
      const rows = lines.slice(1).map(l => { const values = l.split(','); const row: any = {}; headers.forEach((h, i) => row[h] = values[i]?.trim() || ''); return row; });
      const uploadId = `upload_${Date.now()}`;
      uploads.set(uploadId, { id: uploadId, filename: file.name, uploadedAt: new Date().toISOString(), rowCount: rows.length, status: 'processed', fileType, headers, sampleData: rows.slice(0, 10) });
      return new Response(JSON.stringify({ uploadId, filename: file.name, rowCount: rows.length, status: 'processed', headers, sampleData: preview ? rows.slice(0, 5) : undefined }), { headers: corsHeaders });
    }
    return new Response(JSON.stringify(Array.from(uploads.values())), { headers: corsHeaders });
  }

  // Emission Factors
  if (url.pathname === '/api/factors' || url.pathname === '/api/v1/factors') {
    if (request.method === 'GET') {
      const factors = Array.from(emissionFactors.values());
      return new Response(JSON.stringify(factors), { headers: corsHeaders });
    }
    if (request.method === 'POST') {
      const body = await request.json();
      const id = `ef_${Date.now()}`;
      const factor = { id, ...body, createdAt: new Date().toISOString() };
      emissionFactors.set(id, factor);
      return new Response(JSON.stringify(factor), { headers: corsHeaders });
    }
  }

  // Emission Factor by ID
  if (url.pathname.match(/^\/api\/factors\/[^\/]+$/)) {
    const factorId = url.pathname.split('/').pop();
    const factor = emissionFactors.get(factorId);
    if (!factor) return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: corsHeaders });
    if (request.method === 'DELETE') { emissionFactors.delete(factorId); return new Response(JSON.stringify({ deleted: factorId }), { headers: corsHeaders }); }
    if (request.method === 'PUT') { const body = await request.json(); emissionFactors.set(factorId, { ...factor, ...body }); return new Response(JSON.stringify({ ...factor, ...body }), { headers: corsHeaders }); }
    return new Response(JSON.stringify(factor), { headers: corsHeaders });
  }

  return new Response(JSON.stringify({ message: 'CO2 Emission API v1.0.0-MVP', endpoints: ['/health', '/api/dashboard/summary', '/api/v1/calculations', '/api/v1/uploads', '/api/v1/factors'] }), { headers: corsHeaders });
}

function calcWithMapping(rows: any[], mapping: any, fileType: string) {
  const factors: any = { accounting: { '電気': { s: 2, f: 0.453 }, 'ガソリン': { s: 1, f: 2.32 }, '軽油': { s: 1, f: 2.58 }, 'ガス': { s: 1, f: 2.21 } }, sales: { '製品': { s: 3, f: 0.5 } }, pos: { 'エコ': { s: 3, f: 2.0 }, '水筒': { s: 3, f: 1.5 }, '箸': { s: 3, f: 0.1 } } };
  const f = factors[fileType] || factors.accounting;
  let s1 = 0, s2 = 0, s3 = 0;
  rows.forEach(r => { const subject = r[mapping['subject']] || r[mapping['product']] || r[mapping['product_name']] || ''; const amount = parseFloat(r[mapping['amount']] || r[mapping['quantity']] || '0') || 0; let factor = 1, scope = 3; for (const [k, v] of Object.entries(f)) { if (subject.includes(k)) { factor = (v as any).f; scope = (v as any).s; break; } } const e = amount * factor; if (scope === 1) s1 += e; else if (scope === 2) s2 += e; else s3 += e; });
  return { scope1: s1, scope2: s2, scope3: s3, total: s1 + s2 + s3 };
}

function createBreakdown(rows: any[], mapping: any, fileType: string) {
  const factors: any = { accounting: { '電気': { s: 2, f: 0.453, name: '電気（日本）' }, 'ガソリン': { s: 1, f: 2.32, name: 'ガソリン' }, '軽油': { s: 1, f: 2.58, name: '軽油' }, 'ガス': { s: 1, f: 2.21, name: '都市ガス' } }, sales: { '製品': { s: 3, f: 0.5, name: '製品 A（標準）' } }, pos: { 'エコ': { s: 3, f: 2.0, name: 'エコバッグ' }, '水筒': { s: 3, f: 1.5, name: '水筒' }, '箸': { s: 3, f: 0.1, name: '箸セット' } } };
  const f = factors[fileType] || factors.accounting;
  const breakdown: any[] = [];
  rows.forEach((r, i) => { const subject = r[mapping['subject']] || r[mapping['product']] || r[mapping['product_name']] || r[Object.keys(r)[1]] || ''; const amount = parseFloat(r[mapping['amount']] || r[mapping['quantity']] || Object.values(r)[2] || '0') || 0; let factor = 1, scope = 3, factorName = '標準'; for (const [k, v] of Object.entries(f)) { if (subject.includes(k)) { factor = (v as any).f; scope = (v as any).s; factorName = (v as any).name; break; } } const emission = amount * factor; breakdown.push({ row: i + 1, subject, amount, factor, factorName, scope, emission }); });
  return breakdown;
}
