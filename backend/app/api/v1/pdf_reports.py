"""PDF レポート出力 API"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.db.session import SessionLocal
from app.db.base import CalculationJob, ScopeSummary, CalculationResult

router = APIRouter()


@router.get("/jobs/{job_id}/pdf", response_class=HTMLResponse, summary="PDF レポート出力（HTML 印刷）")
def generate_pdf_report(job_id: str):
    """算出結果の PDF レポートを生成（HTML 印刷経由）"""
    db = SessionLocal()
    try:
        job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        summary = db.query(ScopeSummary).filter(ScopeSummary.job_id == job_id).first()
        results = db.query(CalculationResult).filter(
            CalculationResult.job_id == job_id,
            CalculationResult.status == "calculated"
        ).limit(100).all()
        
        # カテゴリ別集計
        category_summary = {}
        for r in results:
            cat = r.activity_type or "unknown"
            if cat not in category_summary:
                category_summary[cat] = {"total": 0.0, "count": 0, "scope": r.scope}
            category_summary[cat]["total"] += r.amount_kg_co2e or 0.0
            category_summary[cat]["count"] += 1
        
        # HTML レポート生成
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>CO2 排出量レポート</title>
    <style>
        @media print {{
            @page {{ size: A4; margin: 20mm; }}
            body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .no-print {{ display: none; }}
        }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ font-size: 24px; color: #1a1a1a; border-bottom: 3px solid #0070f3; padding-bottom: 10px; }}
        h2 {{ font-size: 18px; color: #333; margin-top: 30px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
        .meta {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .meta p {{ margin: 5px 0; font-size: 14px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-card.s1 {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }}
        .stat-card.s2 {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }}
        .stat-card.s3 {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; }}
        .stat-card .label {{ font-size: 12px; opacity: 0.9; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }}
        th {{ background: #f0f0f0; padding: 10px 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .badge-s1 {{ background: #fee2e2; color: #dc2626; }}
        .badge-s2 {{ background: #fef3c7; color: #d97706; }}
        .badge-s3 {{ background: #dbeafe; color: #2563eb; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #e0e0e0; font-size: 12px; color: #888; text-align: center; }}
        .btn {{ background: #0070f3; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 14px; cursor: pointer; margin: 10px 5px; }}
        .btn:hover {{ background: #005dd4; }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin: 20px 0;">
        <button class="btn" onclick="window.print()">🖨️ PDF として保存</button>
        <button class="btn" onclick="window.close()">閉じる</button>
    </div>

    <h1>🌍 CO2 排出量レポート</h1>
    
    <div class="meta">
        <p><strong>レポート ID:</strong> {job_id}</p>
        <p><strong>発行日:</strong> {job.completed_at.strftime('%Y年%m月%d日 %H:%M') if job.completed_at else 'N/A'}</p>
        <p><strong>排出係数バージョン:</strong> {job.emission_factor_version}</p>
        <p><strong>対象行数:</strong> {summary.total_row_count if summary else 0}行（分類済：{summary.calculated_row_count if summary else 0} / 未分類：{summary.unclassified_count if summary else 0}）</p>
    </div>

    <h2>📊 排出量サマリー</h2>
    <div class="stats">
        <div class="stat-card">
            <div class="value">{(summary.grand_total if summary else 0):,.1f}</div>
            <div class="label">総排出量 (kg-CO2e)</div>
        </div>
        <div class="stat-card s1">
            <div class="value">{(summary.scope1_total if summary else 0):,.1f}</div>
            <div class="label">Scope 1</div>
        </div>
        <div class="stat-card s2">
            <div class="value">{(summary.scope2_total if summary else 0):,.1f}</div>
            <div class="label">Scope 2</div>
        </div>
        <div class="stat-card s3">
            <div class="value">{(summary.scope3_total if summary else 0):,.1f}</div>
            <div class="label">Scope 3</div>
        </div>
    </div>

    <h2>📦 カテゴリ別内訳</h2>
    <table>
        <thead>
            <tr><th>カテゴリ</th><th>排出量 (kg-CO2e)</th><th>件数</th><th>Scope</th></tr>
        </thead>
        <tbody>
"""
        
        for cat, data in sorted(category_summary.items(), key=lambda x: -x[1]['total']):
            scope_badge = f"badge-s{data['scope']}"
            html += f"""            <tr>
                <td><strong>{cat}</strong></td>
                <td>{data['total']:,.2f}</td>
                <td>{data['count']}</td>
                <td><span class="badge {scope_badge}">Scope {data['scope']}</span></td>
            </tr>
"""
        
        html += f"""        </tbody>
    </table>

    <h2>📋 行別詳細（最大 100 件）</h2>
    <table>
        <thead>
            <tr><th>#</th><th>活動種別</th><th>活動量</th><th>係数</th><th>Scope</th><th>排出量 (kg-CO2e)</th></tr>
        </thead>
        <tbody>
"""
        
        for i, r in enumerate(results, 1):
            scope_badge = f"badge-s{r.scope}" if r.scope else ""
            scope_label = f"Scope {r.scope}" if r.scope else "-"
            html += f"""            <tr>
                <td>{i}</td>
                <td>{r.activity_type or '-'}</td>
                <td>{r.activity_amount or 0} {r.activity_unit or ''}</td>
                <td>{r.emission_factor_value or 0}</td>
                <td><span class="badge {scope_badge}">{scope_label}</span></td>
                <td><strong>{(r.amount_kg_co2e or 0):,.3f}</strong></td>
            </tr>
"""
        
        html += f"""        </tbody>
    </table>

    <div class="footer">
        <p>本レポートは CO2 Emission PoC システムにより自動生成されました</p>
        <p>発行元：CO2 Emission Calculator | レポート ID: {job_id}</p>
    </div>

    <script>
        // 初回表示時に印刷ダイアログを自動表示（オプション）
        // window.onload = () => {{ window.print(); }};
    </script>
</body>
</html>"""
        
        return HTMLResponse(content=html, media_type="text/html")
    finally:
        db.close()
