const uploads = new Map<string, any>();
const calculations = new Map<string, any>();
const emissionFactors = new Map<string, any>();

// 排出係数 DB - 環境省・IEA・EPA 公式データに基づく
const initialFactors = [
  // === 環境省 排出係数（日本）===
  // エネルギー（電気）
  { id: 'jp_moe_001', name: '電気（日本全国平均）', source: '環境省 2023 年度版', scope: 2, factor: 0.453, unit: 'kWh', country: 'JP', category: 'energy', validFrom: '2023-04-01', validTo: '2024-03-31', description: '電源構成に基づく排出係数' },
  { id: 'jp_moe_002', name: '電気（東京電力）', source: '環境省 2023 年度版', scope: 2, factor: 0.438, unit: 'kWh', country: 'JP', category: 'energy', validFrom: '2023-04-01', validTo: '2024-03-31', description: '東京電力エリア' },
  { id: 'jp_moe_003', name: '電気（関西電力）', source: '環境省 2023 年度版', scope: 2, factor: 0.424, unit: 'kWh', country: 'JP', category: 'energy', validFrom: '2023-04-01', validTo: '2024-03-31', description: '関西電力エリア（原子力比率高）' },
  { id: 'jp_moe_004', name: '電気（中部電力）', source: '環境省 2023 年度版', scope: 2, factor: 0.449, unit: 'kWh', country: 'JP', category: 'energy', validFrom: '2023-04-01', validTo: '2024-03-31', description: '中部電力エリア' },
  
  // 燃料（Scope 1）
  { id: 'jp_moe_010', name: 'ガソリン（自動車）', source: '環境省 2023 年度版', scope: 1, factor: 2.32, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '自動車用ガソリン燃焼' },
  { id: 'jp_moe_011', name: '軽油（自動車）', source: '環境省 2023 年度版', scope: 1, factor: 2.58, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '自動車用軽油燃焼' },
  { id: 'jp_moe_012', name: '重油（A 重油）', source: '環境省 2023 年度版', scope: 1, factor: 2.78, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '産業用重油' },
  { id: 'jp_moe_013', name: '都市ガス（13A）', source: '環境省 2023 年度版', scope: 1, factor: 2.21, unit: 'm3', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '家庭用・業務用都市ガス' },
  { id: 'jp_moe_014', name: 'LP ガス（プロパン）', source: '環境省 2023 年度版', scope: 1, factor: 3.06, unit: 'kg', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: 'LP ガス燃焼' },
  { id: 'jp_moe_015', name: '灯油', source: '環境省 2023 年度版', scope: 1, factor: 2.48, unit: 'L', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '暖房用灯油' },
  { id: 'jp_moe_016', name: '石炭（一般炭）', source: '環境省 2023 年度版', scope: 1, factor: 2.48, unit: 'kg', country: 'JP', category: 'fuel', validFrom: '2023-04-01', validTo: '2024-03-31', description: '火力発電・産業用' },
  
  // 製品・サービス（Scope 3）
  { id: 'jp_idea_001', name: '製品 A（標準）', source: 'IDEA 2023', scope: 3, factor: 0.5, unit: 'kg', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: '一般製品（標準）' },
  { id: 'jp_idea_002', name: 'エコバッグ', source: 'IDEA 2023', scope: 3, factor: 2.0, unit: '個', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: '布製エコバッグ' },
  { id: 'jp_idea_003', name: '水筒', source: 'IDEA 2023', scope: 3, factor: 1.5, unit: '個', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'ステンレス水筒' },
  { id: 'jp_idea_004', name: '箸セット', source: 'IDEA 2023', scope: 3, factor: 0.1, unit: '個', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: '割り箸' },
  { id: 'jp_idea_005', name: '紙（コピー用紙）', source: 'IDEA 2023', scope: 3, factor: 1.2, unit: 'kg', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'A4 コピー用紙' },
  { id: 'jp_idea_006', name: 'プラスチック容器', source: 'IDEA 2023', scope: 3, factor: 3.5, unit: 'kg', country: 'JP', category: 'product', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'PET 容器' },
  
  // 交通（Scope 3）
  { id: 'jp_moe_020', name: '鉄道（新幹線）', source: '環境省 2023 年度版', scope: 3, factor: 0.019, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: '新幹線（乗客 1 人 km）' },
  { id: 'jp_moe_021', name: '鉄道（在来線）', source: '環境省 2023 年度版', scope: 3, factor: 0.017, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: 'JR 在来線（乗客 1 人 km）' },
  { id: 'jp_moe_022', name: '地下鉄', source: '環境省 2023 年度版', scope: 3, factor: 0.008, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: '地下鉄（乗客 1 人 km）' },
  { id: 'jp_moe_023', name: 'バス', source: '環境省 2023 年度版', scope: 3, factor: 0.089, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: '路線バス（乗客 1 人 km）' },
  { id: 'jp_moe_024', name: 'タクシー', source: '環境省 2023 年度版', scope: 3, factor: 0.14, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: 'タクシー（乗客 1 人 km）' },
  { id: 'jp_moe_025', name: '航空機（国内線）', source: '環境省 2023 年度版', scope: 3, factor: 0.11, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: '国内線（乗客 1 人 km）' },
  { id: 'jp_moe_026', name: '航空機（国際線）', source: '環境省 2023 年度版', scope: 3, factor: 0.09, unit: 'km', country: 'JP', category: 'transport', validFrom: '2023-04-01', validTo: '2024-03-31', description: '国際線（乗客 1 人 km）' },
  
  // === IEA（国際エネルギー機関）===
  { id: 'iea_001', name: 'Electricity (World Avg)', source: 'IEA 2023', scope: 2, factor: 0.475, unit: 'kWh', country: 'INTL', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'World average electricity emission factor' },
  { id: 'iea_002', name: 'Electricity (US)', source: 'IEA 2023', scope: 2, factor: 0.386, unit: 'kWh', country: 'US', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'US electricity emission factor' },
  { id: 'iea_003', name: 'Electricity (China)', source: 'IEA 2023', scope: 2, factor: 0.570, unit: 'kWh', country: 'CN', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'China electricity emission factor' },
  { id: 'iea_004', name: 'Electricity (EU)', source: 'IEA 2023', scope: 2, factor: 0.295, unit: 'kWh', country: 'EU', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'EU electricity emission factor' },
  { id: 'iea_005', name: 'Natural Gas', source: 'IEA 2023', scope: 1, factor: 2.0, unit: 'm3', country: 'INTL', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'Natural gas combustion' },
  { id: 'iea_006', name: 'Coal (Steam)', source: 'IEA 2023', scope: 1, factor: 2.76, unit: 'kg', country: 'INTL', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'Steam coal combustion' },
  
  // === EPA（米国環境保護庁）===
  { id: 'epa_001', name: 'Gasoline (US)', source: 'EPA 2023', scope: 1, factor: 2.31, unit: 'L', country: 'US', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'Motor gasoline combustion' },
  { id: 'epa_002', name: 'Diesel (US)', source: 'EPA 2023', scope: 1, factor: 2.68, unit: 'L', country: 'US', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'Diesel fuel combustion' },
  { id: 'epa_003', name: 'Propane (US)', source: 'EPA 2023', scope: 1, factor: 2.97, unit: 'kg', country: 'US', category: 'fuel', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'Propane combustion' },
  { id: 'epa_004', name: 'Electricity (US Avg)', source: 'EPA eGRID 2023', scope: 2, factor: 0.393, unit: 'kWh', country: 'US', category: 'energy', validFrom: '2023-01-01', validTo: '2024-12-31', description: 'US national average electricity' },
];

initialFactors.forEach(f => emissionFactors.set(f.id, f));

const corsHeaders = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  
  if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

  // Health
  if (url.pathname === '/api/health' || url.pathname === '/health') {
    return new Response(JSON.stringify({ status: 'ok', version: '1.1.0-mvp', timestamp: new Date().toISOString(), factorsCount: emissionFactors.size }), { headers: corsHeaders });
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

  // Scope Info
  if (url.pathname === '/api/scope-info' || url.pathname === '/api/v1/scope-info') {
    return new Response(JSON.stringify({
      scope1: { title: 'Scope 1', titleJa: '直接排出', description: '自社で直接燃焼・排出する温室効果ガス。例：ボイラー、車両、社有施設の燃料燃焼', examples: ['ガソリン燃焼', '軽油燃焼', '都市ガス', '重油', '石炭', 'LP ガス'] },
      scope2: { title: 'Scope 2', titleJa: '間接排出（エネルギー）', description: '他社から供給された電気・熱・蒸気の使用に伴う排出。例：オフィス・工場の電気使用', examples: ['電気使用', '熱供給', '蒸気使用'] },
      scope3: { title: 'Scope 3', titleJa: 'その他の間接排出', description: 'バリューチェーン全体のその他の間接排出。例：出張、購入品、廃棄物', examples: ['出張（航空機・鉄道）', '購入品', '廃棄物処理', '通勤'] }
    }), { headers: corsHeaders });
  }

  return new Response(JSON.stringify({ message: 'CO2 Emission API v1.1.0-MVP', endpoints: ['/health', '/api/dashboard/summary', '/api/v1/calculations', '/api/v1/uploads', '/api/v1/factors', '/api/v1/scope-info'] }), { headers: corsHeaders });
}

function calcWithMapping(rows: any[], mapping: any, fileType: string) {
  const factors: any = { accounting: { '電気': { s: 2, f: 0.453 }, 'ガソリン': { s: 1, f: 2.32 }, '軽油': { s: 1, f: 2.58 }, 'ガス': { s: 1, f: 2.21 }, '重油': { s: 1, f: 2.78 }, 'LP': { s: 1, f: 3.06 }, '灯油': { s: 1, f: 2.48 }, '石炭': { s: 1, f: 2.48 } }, sales: { '製品': { s: 3, f: 0.5 } }, pos: { 'エコ': { s: 3, f: 2.0 }, '水筒': { s: 3, f: 1.5 }, '箸': { s: 3, f: 0.1 }, '紙': { s: 3, f: 1.2 }, 'プラ': { s: 3, f: 3.5 } } };
  const f = factors[fileType] || factors.accounting;
  let s1 = 0, s2 = 0, s3 = 0;
  rows.forEach(r => { const subject = r[mapping['subject']] || r[mapping['product']] || r[mapping['product_name']] || ''; const amount = parseFloat(r[mapping['amount']] || r[mapping['quantity']] || '0') || 0; let factor = 1, scope = 3; for (const [k, v] of Object.entries(f)) { if (subject.includes(k)) { factor = (v as any).f; scope = (v as any).s; break; } } const e = amount * factor; if (scope === 1) s1 += e; else if (scope === 2) s2 += e; else s3 += e; });
  return { scope1: s1, scope2: s2, scope3: s3, total: s1 + s2 + s3 };
}

function createBreakdown(rows: any[], mapping: any, fileType: string) {
  const factors: any = { accounting: { '電気': { s: 2, f: 0.453, name: '電気（日本）' }, 'ガソリン': { s: 1, f: 2.32, name: 'ガソリン' }, '軽油': { s: 1, f: 2.58, name: '軽油' }, 'ガス': { s: 1, f: 2.21, name: '都市ガス' }, '重油': { s: 1, f: 2.78, name: '重油' }, 'LP': { s: 1, f: 3.06, name: 'LP ガス' }, '灯油': { s: 1, f: 2.48, name: '灯油' }, '石炭': { s: 1, f: 2.48, name: '石炭' } }, sales: { '製品': { s: 3, f: 0.5, name: '製品 A（標準）' } }, pos: { 'エコ': { s: 3, f: 2.0, name: 'エコバッグ' }, '水筒': { s: 3, f: 1.5, name: '水筒' }, '箸': { s: 3, f: 0.1, name: '箸セット' }, '紙': { s: 3, f: 1.2, name: 'コピー用紙' }, 'プラ': { s: 3, f: 3.5, name: 'プラスチック容器' } } };
  const f = factors[fileType] || factors.accounting;
  const breakdown: any[] = [];
  rows.forEach((r, i) => { const subject = r[mapping['subject']] || r[mapping['product']] || r[mapping['product_name']] || r[Object.keys(r)[1]] || ''; const amount = parseFloat(r[mapping['amount']] || r[mapping['quantity']] || Object.values(r)[2] || '0') || 0; let factor = 1, scope = 3, factorName = '標準'; for (const [k, v] of Object.entries(f)) { if (subject.includes(k)) { factor = (v as any).f; scope = (v as any).s; factorName = (v as any).name; break; } } const emission = amount * factor; breakdown.push({ row: i + 1, subject, amount, factor, factorName, scope, emission }); });
  return breakdown;
}
