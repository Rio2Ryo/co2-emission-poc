export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // CORS headers
  const corsHeaders = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  // Handle OPTIONS for CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  // Health check
  if (url.pathname === '/api/health' || url.pathname === '/health') {
    return new Response(JSON.stringify({ 
      status: 'ok', 
      version: '0.1.0',
      timestamp: new Date().toISOString()
    }), { headers: corsHeaders });
  }

  // Dashboard summary - with test data
  if (url.pathname === '/api/dashboard/summary' || url.pathname === '/api/v1/dashboard/summary') {
    const summary = {
      total_calculations: 3,
      total_emissions_kg: 2847.5,
      scope1_kg: 1245.0,
      scope2_kg: 1102.5,
      scope3_kg: 500.0,
      last_updated: new Date().toISOString(),
      trend: 'increasing'
    };
    return new Response(JSON.stringify(summary), { headers: corsHeaders });
  }

  // Calculations list
  if (url.pathname === '/api/calculations' || url.pathname === '/api/v1/calculations') {
    const calculations = [
      {
        id: 'calc_001',
        created_at: '2024-03-01T10:00:00Z',
        source_type: 'accounting',
        grand_total_kg: 1245.5,
        scope1: 563.5,
        scope2: 482.0,
        scope3: 200.0,
        status: 'completed'
      },
      {
        id: 'calc_002',
        created_at: '2024-03-05T14:30:00Z',
        source_type: 'sales',
        grand_total_kg: 856.0,
        scope1: 325.5,
        scope2: 330.5,
        scope3: 200.0,
        status: 'completed'
      },
      {
        id: 'calc_003',
        created_at: '2024-03-10T09:15:00Z',
        source_type: 'pos',
        grand_total_kg: 746.0,
        scope1: 356.0,
        scope2: 290.0,
        scope3: 100.0,
        status: 'completed'
      }
    ];
    return new Response(JSON.stringify(calculations), { headers: corsHeaders });
  }

  // Uploads list
  if (url.pathname === '/api/uploads' || url.pathname === '/api/v1/uploads') {
    const uploads = [
      {
        id: 'upload_001',
        filename: 'accounting_test.csv',
        uploaded_at: '2024-03-01T09:00:00Z',
        row_count: 8,
        status: 'processed'
      },
      {
        id: 'upload_002',
        filename: 'sales_test.csv',
        uploaded_at: '2024-03-05T14:00:00Z',
        row_count: 6,
        status: 'processed'
      },
      {
        id: 'upload_003',
        filename: 'pos_test.csv',
        uploaded_at: '2024-03-10T08:30:00Z',
        row_count: 5,
        status: 'processed'
      }
    ];
    return new Response(JSON.stringify(uploads), { headers: corsHeaders });
  }

  // Default response
  return new Response(JSON.stringify({
    message: 'CO2 Emission API - Demo Mode',
    note: 'Test data is loaded. Full backend coming soon.',
    available_endpoints: [
      '/health',
      '/api/dashboard/summary',
      '/api/v1/calculations',
      '/api/v1/uploads'
    ]
  }), { headers: corsHeaders });
}
