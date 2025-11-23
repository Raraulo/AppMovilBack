import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from decimal import Decimal
from plotly.offline import plot
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from .models import Producto, Factura, Cliente

# --- Función para generar gráficos ---
def generate_plotly_plot(df, plot_type, x, y, title, colors_list=None, labels=None):
    """Genera gráficos Plotly robustos que se ven incluso con 1 solo dato."""
    
    div_id = "plot_" + re.sub(r'\W+', '', title).lower()
    
    # Configuración básica del Layout para que se vea bien integrado
    layout_config = dict(
        template='plotly_white',
        margin=dict(l=40, r=20, t=60, b=40),
        title=dict(
            text=title,
            font=dict(size=18, color='#333', family="Segoe UI, sans-serif")
        ),
        font=dict(color='#555'),
        paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente
        plot_bgcolor='rgba(0,0,0,0)',
        height=450, # Altura forzada desde Python
        xaxis=dict(showgrid=False, showline=True, linewidth=1, linecolor='#ddd'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        hoverlabel=dict(bgcolor="white", font_size=13)
    )

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos disponibles", showarrow=False, font=dict(size=16, color="#999"))
        fig.update_layout(**layout_config)
    else:
        # Definir colores
        colors = colors_list if colors_list else ['#667eea']
        
        # Crear el gráfico
        fig = px.line(df, x=x, y=y, labels=labels, color_discrete_sequence=colors)
        
        # ✅ CLAVE: 'lines+markers' asegura que se vea algo aunque sea 1 solo punto
        fig.update_traces(mode='lines+markers', line=dict(width=3), marker=dict(size=10, line=dict(width=2, color='white')))
        
        # Efecto de área sombreada debajo de la línea (opcional, se ve moderno)
        fig.update_traces(fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.1)')
        
        fig.update_layout(**layout_config)
    
    # Generar el HTML del div (Sin incluir JS aquí para no duplicar)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False, auto_play=False, config={'responsive': True, 'displayModeBar': False})
    
    # Inyectar el ID correcto
    plot_div = re.sub(r'id="[^"]+"', f'id="{div_id}"', plot_div, count=1)
    
    return plot_div

@staff_member_required
def custom_dashboard(request):
    # --- 1. MÉTRICAS ---
    ventas_totales = Factura.objects.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    ordenes_totales = Factura.objects.count()
    clientes_totales = Cliente.objects.count()
    productos_total = Producto.objects.count()
    # Productos agotados
    productos_agotados = Producto.objects.filter(stock__lte=0).count()
    
    # Ticket promedio
    if ordenes_totales > 0:
        ticket_promedio = ventas_totales / ordenes_totales
    else:
        ticket_promedio = Decimal('0.00')

    # --- 2. GRÁFICO: Ventas Diarias ---
    plot_ventas_diarias = None
    try:
        # Traer datos de los últimos 30 días
        hace_30_dias = timezone.now() - datetime.timedelta(days=30)
        ventas_qs = Factura.objects.filter(fecha__gte=hace_30_dias)\
            .annotate(dia=TruncDate('fecha'))\
            .values('dia')\
            .annotate(total=Sum('total'))\
            .order_by('dia')
        
        df = pd.DataFrame(list(ventas_qs))
        
        if not df.empty:
            # Convertir fechas correctamente
            df['dia'] = pd.to_datetime(df['dia'])
            # Formatear para el eje X
            df['fecha_str'] = df['dia'].dt.strftime('%d %b')
            
            plot_ventas_diarias = generate_plotly_plot(
                df, 'line', x='fecha_str', y='total',
                title='Comportamiento de Ventas (30 Días)',
                colors_list=['#3B82F6'], # Azul vibrante
                labels={'fecha_str': 'Fecha', 'total': 'Ventas (€)'}
            )
    except Exception as e:
        print(f"Error generando gráfico: {e}")

    context = {
        'ventas_totales': f"€{ventas_totales:,.2f}",
        'ordenes_totales': ordenes_totales,
        'ticket_promedio': f"€{ticket_promedio:,.2f}",
        'clientes_totales': clientes_totales,
        'productos_total': productos_total,
        'productos_agotados': productos_agotados,
        'plot_ventas_diarias': plot_ventas_diarias,
    }
    
    return render(request, 'admin/custom_dashboard.html', context)