import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from datetime import datetime
import os
import json
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart

def detect_excel_structure(df):
    """
    اكتشاف بنية ملف الإكسل وتحديد الأعمدة المهمة
    
    المعلمات:
        df (DataFrame): إطار بيانات pandas يحتوي على البيانات المالية الخام
        
    العوائد:
        dict: قاموس يربط الأعمدة المعروفة بأسماء الأعمدة الفعلية في الملف
    """
    # إعداد قاموس فارغ لتعيين الأعمدة
    column_mapping = {}
    
    # قائمة بالأسماء المحتملة للأعمدة
    date_columns = ['Date', 'Transaction Date', 'تاريخ', 'تاريخ المعاملة', 'التاريخ', 'date', 'datetime', 'time']
    description_columns = ['Description', 'Transaction Details', 'وصف', 'تفاصيل المعاملة', 'الوصف', 'البيان', 'التفاصيل', 'desc', 'details']
    category_columns = ['Category', 'Type', 'فئة', 'تصنيف', 'نوع', 'cat', 'group', 'مجموعة', 'النوع']
    income_columns = ['Income', 'Credit', 'دخل', 'إيرادات', 'ايرادات', 'مدين', 'credit', 'in', 'revenue', 'دائن', 'دخل']
    expense_columns = ['Expense', 'Expenses', 'Debit', 'مصروفات', 'مصاريف', 'دائن', 'debit', 'out', 'مصرف', 'مصروف', 'خصم']
    
    # البحث في أسماء الأعمدة
    for col in df.columns:
        col_str = str(col).lower()
        
        if any(date_col.lower() in col_str for date_col in date_columns) and 'Date' not in column_mapping:
            column_mapping['Date'] = col
        elif any(desc_col.lower() in col_str for desc_col in description_columns) and 'Description' not in column_mapping:
            column_mapping['Description'] = col
        elif any(cat_col.lower() in col_str for cat_col in category_columns) and 'Category' not in column_mapping:
            column_mapping['Category'] = col
        elif any(income_col.lower() in col_str for income_col in income_columns) and 'Income' not in column_mapping:
            column_mapping['Income'] = col
        elif any(expense_col.lower() in col_str for expense_col in expense_columns) and 'Expenses' not in column_mapping:
            column_mapping['Expenses'] = col
    
    return column_mapping

def analyze_excel_data(df, column_mapping):
    """
    تحليل بيانات الإكسل وتنظيفها وتحويلها إلى تنسيق موحد
    
    المعلمات:
        df (DataFrame): إطار بيانات pandas يحتوي على البيانات المالية
        column_mapping (dict): قاموس يربط الأعمدة المعروفة بأسماء الأعمدة الفعلية في الملف
        
    العوائد:
        DataFrame: إطار بيانات منظم ومعالج
    """
    # إنشاء نسخة من البيانات
    data = df.copy()
    
    # إنشاء إطار بيانات جديد للنتائج
    processed_data = pd.DataFrame()
    
    # معالجة عمود التاريخ
    if 'Date' in column_mapping and column_mapping['Date'] is not None:
        processed_data['Date'] = data[column_mapping['Date']]
        # محاولة تحويل التاريخ إلى نوع datetime
        processed_data['Date'] = pd.to_datetime(processed_data['Date'], errors='coerce')
    else:
        # إنشاء تواريخ افتراضية باستخدام مؤشر البيانات
        current_date = datetime.now()
        date_range = pd.date_range(end=current_date, periods=len(data), freq='D')
        processed_data['Date'] = date_range
    
    # معالجة عمود الوصف
    if 'Description' in column_mapping and column_mapping['Description'] is not None:
        processed_data['Description'] = data[column_mapping['Description']]
    else:
        # إذا لم يتم العثور على عمود الوصف، استخدم عمود رقم الصف
        processed_data['Description'] = [f"المعاملة #{i+1}" for i in range(len(data))]
    
    # معالجة عمود الإيرادات
    if 'Income' in column_mapping and column_mapping['Income'] is not None:
        income_col = data[column_mapping['Income']]
        # التحويل إلى قيم رقمية
        processed_data['Income'] = pd.to_numeric(income_col, errors='coerce').fillna(0)
    else:
        processed_data['Income'] = 0
    
    # معالجة عمود المصروفات
    if 'Expenses' in column_mapping and column_mapping['Expenses'] is not None:
        expense_col = data[column_mapping['Expenses']]
        # التحويل إلى قيم رقمية
        processed_data['Expenses'] = pd.to_numeric(expense_col, errors='coerce').fillna(0)
        
        # التأكد من أن المصروفات دائماً موجبة
        processed_data['Expenses'] = processed_data['Expenses'].abs()
    else:
        processed_data['Expenses'] = 0
    
    # معالجة عمود الفئة
    if 'Category' in column_mapping and column_mapping['Category'] is not None:
        processed_data['Category'] = data[column_mapping['Category']]
    else:
        # استخدام التصنيف التقليدي
        processed_data['Category'] = processed_data.apply(lambda row: classify_transactions(row), axis=1)
    
    # تنظيف عمود الفئة
    processed_data['Category'] = processed_data['Category'].astype(str)
    processed_data['Category'] = processed_data['Category'].fillna("غير مصنف")
    processed_data['Category'] = processed_data['Category'].replace('', "غير مصنف")
    processed_data['Category'] = processed_data['Category'].replace('nan', "غير مصنف")
    
    # إضافة عمود لصافي التدفق النقدي
    processed_data['Net'] = processed_data['Income'] - processed_data['Expenses']
    
    # تنظيف البيانات
    processed_data = processed_data.dropna(subset=['Date'])
    
    return processed_data

def classify_transactions(row):
    """
    تصنيف المعاملات بناءً على البيانات المتاحة
    
    المعلمات:
        row (Series): صف من إطار البيانات يحتوي على معاملة واحدة
        
    العوائد:
        str: فئة المعاملة المصنفة
    """
    # الكلمات المفتاحية للفئات المختلفة
    category_keywords = {
        'رواتب': ['راتب', 'معاش', 'أجر', 'salary', 'wage', 'payroll'],
        'تبرعات': ['تبرع', 'هبة', 'دعم', 'donation', 'grant', 'support'],
        'استثمارات': ['أرباح', 'استثمار', 'عائد', 'dividend', 'investment', 'return'],
        'مبيعات': ['مبيعات', 'بيع', 'إيراد', 'sales', 'revenue', 'income'],
        'مصاريف تشغيلية': ['تشغيل', 'صيانة', 'خدمة', 'operation', 'maintenance', 'service'],
        'مصاريف إدارية': ['إدارة', 'مكتب', 'إيجار', 'administration', 'office', 'rent'],
        'مصاريف تسويقية': ['تسويق', 'إعلان', 'دعاية', 'marketing', 'advertising', 'promotion'],
        'مصاريف الموظفين': ['موظف', 'تأمين', 'تدريب', 'employee', 'insurance', 'training'],
        'مصاريف مالية': ['بنك', 'فائدة', 'رسوم', 'bank', 'interest', 'fees'],
        'مشتريات': ['شراء', 'مشتريات', 'بضاعة', 'purchase', 'goods', 'inventory'],
        'سفر': ['سفر', 'تذكرة', 'فندق', 'travel', 'ticket', 'hotel']
    }
    
    # تحديد ما إذا كانت معاملة دخل أو مصروفات
    is_income = False
    is_expense = False
    
    if 'Income' in row and row['Income'] > 0:
        is_income = True
    
    if 'Expenses' in row and row['Expenses'] > 0:
        is_expense = True
    
    # إذا كان لدينا وصف، استخدمه للتصنيف
    if 'Description' in row and pd.notna(row['Description']) and row['Description'] != '':
        description = str(row['Description']).lower()
        
        # التحقق من كل فئة
        for category, keywords in category_keywords.items():
            if any(keyword in description for keyword in keywords):
                # تعديل الفئة بناءً على نوع المعاملة
                if is_income and not category.startswith('مصاريف') and not category == 'مشتريات' and not category == 'سفر':
                    return category
                elif is_expense and (category.startswith('مصاريف') or category == 'مشتريات' or category == 'سفر'):
                    return category
    
    # إذا لم يتم التصنيف بناءً على الوصف، استخدم التصنيف الافتراضي
    if is_income:
        return "إيرادات أخرى"
    elif is_expense:
        return "مصاريف أخرى"
    else:
        return "غير مصنف"

def generate_ai_insights(data):
    """
    إنشاء تحليلات ورؤى ذكية للبيانات المالية
    
    المعلمات:
        data (DataFrame): إطار بيانات pandas يحتوي على البيانات المالية المعالجة
        
    العوائد:
        dict: قاموس يحتوي على التحليلات والرؤى الذكية
    """
    # التحقق من البيانات
    if data is None or data.empty:
        return {
            "summary": "لا توجد بيانات كافية للتحليل.",
            "insights": ["لا توجد بيانات مالية متاحة للتحليل."],
            "category_analysis": {},
            "trends": {},
            "recommendations": ["يرجى تحميل ملف بيانات مالية صالح للتحليل."]
        }
    
    # حساب الإحصائيات الأساسية
    total_income = data['Income'].sum()
    total_expenses = data['Expenses'].sum()
    net_cash_flow = total_income - total_expenses
    
    # تحليل الفئات
    category_analysis = {}
    
    if 'Category' in data.columns:
        # المصروفات حسب الفئة
        expenses_by_category = data.groupby('Category')['Expenses'].sum()
        # الإيرادات حسب الفئة
        income_by_category = data.groupby('Category')['Income'].sum()
        
        # دمج التحليلات
        for category in set(expenses_by_category.index) | set(income_by_category.index):
            expense = expenses_by_category.get(category, 0)
            income = income_by_category.get(category, 0)
            
            category_analysis[category] = {
                'expenses': float(expense),
                'income': float(income),
                'net': float(income - expense)
            }
    
    # إنشاء الملخص
    if net_cash_flow >= 0:
        summary = f"إجمالي الإيرادات ({total_income:.2f}) أكبر من إجمالي المصروفات ({total_expenses:.2f})، مما يعني أن هناك تدفق نقدي إيجابي بقيمة {net_cash_flow:.2f}."
        insights = ["التدفق النقدي إيجابي، مما يشير إلى حالة مالية جيدة."]
    else:
        summary = f"إجمالي المصروفات ({total_expenses:.2f}) أكبر من إجمالي الإيرادات ({total_income:.2f})، مما يعني أن هناك تدفق نقدي سلبي بقيمة {abs(net_cash_flow):.2f}."
        insights = ["التدفق النقدي سلبي، قد تحتاج إلى مراجعة النفقات أو زيادة الإيرادات."]
    
    # إضافة رؤى إضافية
    if 'Category' in data.columns:
        # الفئة ذات أعلى مصروفات
        top_expense_category = expenses_by_category.idxmax() if not expenses_by_category.empty else "غير متوفر"
        top_expense_value = expenses_by_category.max() if not expenses_by_category.empty else 0
        
        # الفئة ذات أعلى إيرادات
        top_income_category = income_by_category.idxmax() if not income_by_category.empty else "غير متوفر"
        top_income_value = income_by_category.max() if not income_by_category.empty else 0
        
        insights.append(f"أكبر فئة مصروفات هي '{top_expense_category}' بقيمة {top_expense_value:.2f}.")
        insights.append(f"أكبر فئة إيرادات هي '{top_income_category}' بقيمة {top_income_value:.2f}.")
    
    # توصيات بسيطة
    recommendations = []
    
    if net_cash_flow < 0:
        recommendations.append("خفض النفقات في الفئات ذات المصروفات العالية.")
        recommendations.append("البحث عن مصادر إيرادات جديدة لتحسين التدفق النقدي.")
    else:
        recommendations.append("الاستمرار في الحفاظ على التوازن بين الإيرادات والمصروفات.")
        recommendations.append("استثمار الفائض النقدي في مجالات تساعد على نمو الإيرادات.")
    
    # إعداد النتيجة النهائية
    return {
        "summary": summary,
        "insights": insights,
        "category_analysis": category_analysis,
        "trends": {},
        "recommendations": recommendations
    }

def generate_financial_predictions(data, months_ahead=3):
    """
    إنشاء تنبؤات مالية للأشهر القادمة
    
    المعلمات:
        data (DataFrame): إطار بيانات pandas يحتوي على البيانات المالية المعالجة
        months_ahead (int): عدد الأشهر المستقبلية للتنبؤ
        
    العوائد:
        dict: نتائج التنبؤات المالية
    """
    # التحقق من البيانات
    if data is None or data.empty:
        return {
            "summary": "لا توجد بيانات كافية للتنبؤ.",
            "monthly_predictions": []
        }
    
    # تجميع البيانات حسب الشهر
    monthly_data = []
    
    if 'Date' in data.columns and not data['Date'].isna().all():
        try:
            # التأكد من أن عمود التاريخ من نوع datetime
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            
            # تجميع البيانات حسب الشهر
            data_by_month = data.groupby(pd.Grouper(key='Date', freq='M')).agg({
                'Income': 'sum',
                'Expenses': 'sum'
            }).reset_index()
            
            last_date = data_by_month['Date'].max()
            
            # إنشاء تنبؤات باستخدام المتوسط الحسابي البسيط
            avg_income = data_by_month['Income'].mean()
            avg_expenses = data_by_month['Expenses'].mean()
            
            # إنشاء التنبؤات الشهرية
            for i in range(1, months_ahead + 1):
                next_month = last_date + pd.DateOffset(months=i)
                month_str = next_month.strftime('%Y-%m')
                
                predicted_income = avg_income * (1 + (i * 0.01))  # نمو بسيط بنسبة 1% شهرياً
                predicted_expenses = avg_expenses * (1 + (i * 0.005))  # نمو بسيط بنسبة 0.5% شهرياً
                predicted_net = predicted_income - predicted_expenses
                
                monthly_data.append({
                    "month": month_str,
                    "predicted_income": float(predicted_income),
                    "predicted_expenses": float(predicted_expenses),
                    "predicted_net": float(predicted_net),
                    "growth_rate": 0.01
                })
        except Exception as e:
            # في حالة حدوث أي خطأ، إرجاع تنبؤات افتراضية
            for i in range(1, months_ahead + 1):
                next_month = datetime.now() + pd.DateOffset(months=i)
                month_str = next_month.strftime('%Y-%m')
                
                monthly_data.append({
                    "month": month_str,
                    "predicted_income": 0,
                    "predicted_expenses": 0,
                    "predicted_net": 0,
                    "growth_rate": 0
                })
    
    # إنشاء ملخص للتنبؤات
    summary = f"تم إنشاء تنبؤات مالية للـ {months_ahead} أشهر القادمة بناءً على متوسط الإيرادات والمصروفات السابقة مع افتراض نمو بسيط."
    
    return {
        "summary": summary,
        "monthly_predictions": monthly_data
    }

def generate_professional_report(data, ai_analysis=None, report_type="detailed", output_format="pdf"):
    """
    إنشاء تقرير مالي احترافي بتنسيق واضح وجذاب
    
    المعلمات:
        data (DataFrame): إطار بيانات pandas يحتوي على البيانات المالية المعالجة
        ai_analysis (dict): نتائج التحليل الذكي (اختياري)
        report_type (str): نوع التقرير ("summary" أو "detailed")
        output_format (str): تنسيق الإخراج ("pdf" أو "html")
        
    العوائد:
        bytes/str: محتوى التقرير (بايتس للـ PDF، نص للـ HTML)
    """
    try:
        # تسجيل خط عربي (يجب أن يكون متوفراً في المشروع)
        arabic_font_path = os.path.join(os.path.dirname(__file__), "arabic_font.ttf")
        if os.path.exists(arabic_font_path):
            pdfmetrics.registerFont(TTFont('Arabic', arabic_font_path))
        else:
            # محاولة استخدام خط متوفر في النظام يدعم العربية
            try:
                pdfmetrics.registerFont(TTFont('Arabic', "arial.ttf"))
            except:
                # استخدام الخط الافتراضي إذا فشلت كل المحاولات
                pass
        
        # إنشاء أنماط نصية مخصصة
        styles = getSampleStyleSheet()
        
        # أنماط عربية مخصصة
        styles.add(ParagraphStyle(
            name='Arabic-Title',
            fontName='Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=20,
            leading=24,
            alignment=1,  # وسط
            spaceAfter=12
        ))
        
        styles.add(ParagraphStyle(
            name='Arabic-Heading',
            fontName='Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=16,
            leading=18,
            alignment=1,  # وسط
            spaceAfter=10
        ))
        
        styles.add(ParagraphStyle(
            name='Arabic-Body',
            fontName='Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=12,
            leading=14,
            alignment=2,  # يمين (للنص العربي)
            firstLineIndent=20
        ))
        
        styles.add(ParagraphStyle(
            name='Arabic-Table-Header',
            fontName='Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
            fontSize=12,
            alignment=1,  # وسط
            textColor=colors.white
        ))
        
        styles.add(ParagraphStyle(
            name='Arabic-Table-Cell',
            fontName='Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=10,
            alignment=2  # يمين (للنص العربي)
        ))
        
        # إنشاء ملف PDF مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
        
        # إعداد مستند PDF
        doc = SimpleDocTemplate(
            pdf_path, 
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # قائمة العناصر للتقرير
        elements = []
        
        # إضافة شعار أو صورة إن وجدت
        # logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        # if os.path.exists(logo_path):
        #     logo = Image(logo_path)
        #     logo.drawHeight = 1.5*cm
        #     logo.drawWidth = 5*cm
        #     elements.append(logo)
        
        # صفحة العنوان
        current_date = datetime.now().strftime("%Y-%m-%d")
        elements.append(Paragraph("محلل البيانات المالية الذكي", styles['Arabic-Title']))
        elements.append(Spacer(1, 0.5*cm))
        
        report_title = "التقرير المالي المفصل" if report_type == "detailed" else "التقرير المالي الملخص"
        elements.append(Paragraph(report_title, styles['Arabic-Heading']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"تاريخ التقرير: {current_date}", styles['Arabic-Body']))
        
        # إضافة خط تحت العنوان
        elements.append(Spacer(1, 0.5*cm))
        d = Drawing(400, 1)
        d.add(Line(0, 0, 500, 0, strokeColor=colors.navy, strokeWidth=1))
        elements.append(d)
        elements.append(Spacer(1, 1*cm))
        
        # الملخص المالي
        elements.append(Paragraph("ملخص التحليل المالي", styles['Arabic-Heading']))
        elements.append(Spacer(1, 0.5*cm))
        
        # استخراج البيانات الأساسية
        total_income = data['Income'].sum() if 'Income' in data.columns else 0
        total_expenses = data['Expenses'].sum() if 'Expenses' in data.columns else 0
        net_income = total_income - total_expenses
        transaction_count = len(data)
        
        # جدول الملخص المالي
        summary_data = [
            ["البند", "القيمة"],
            ["إجمالي الإيرادات", f"{total_income:,.2f}"],
            ["إجمالي المصروفات", f"{total_expenses:,.2f}"],
            ["صافي الدخل", f"{net_income:,.2f}"],
            ["عدد المعاملات", f"{transaction_count}"]
        ]
        
        # تنسيق الجدول
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'RIGHT'),  # محاذاة يمين للعناوين العربية
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # محاذاة وسط للقيم
            ('FONTNAME', (0, 0), (-1, 0), 'Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))
        
        # إضافة التحليل الذكي إذا كان متاحاً
        if ai_analysis:
            elements.append(Paragraph("التحليل الذكي للبيانات", styles['Arabic-Heading']))
            elements.append(Spacer(1, 0.5*cm))
            
            if 'summary' in ai_analysis and ai_analysis['summary']:
                elements.append(Paragraph(ai_analysis['summary'], styles['Arabic-Body']))
                elements.append(Spacer(1, 0.5*cm))
            
            # إضافة التوصيات والرؤى
            if 'insights' in ai_analysis and ai_analysis['insights']:
                elements.append(Paragraph("التوصيات والرؤى المالية", styles['Arabic-Heading']))
                elements.append(Spacer(1, 0.5*cm))
                
                insights_data = [["#", "التوصية"]]
                for i, insight in enumerate(ai_analysis['insights'], 1):
                    insights_data.append([str(i), insight])
                
                insights_table = Table(insights_data, colWidths=[30, 370], rowHeights=None)
                insights_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # محاذاة يمين للنص العربي
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                elements.append(insights_table)
                elements.append(Spacer(1, 1*cm))
            
            # إضافة تحليل الفئات
            if 'category_analysis' in ai_analysis and ai_analysis['category_analysis']:
                elements.append(Paragraph("تحليل الفئات المالية", styles['Arabic-Heading']))
                elements.append(Spacer(1, 0.5*cm))
                
                category_data = [["الفئة", "الإيرادات", "المصروفات", "الصافي"]]
                
                for category, analysis in ai_analysis['category_analysis'].items():
                    income = analysis.get('income', 0)
                    expenses = analysis.get('expenses', 0)
                    net = analysis.get('net', 0)
                    category_data.append([
                        category, 
                        f"{income:,.2f}", 
                        f"{expenses:,.2f}", 
                        f"{net:,.2f}"
                    ])
                
                category_table = Table(category_data, colWidths=[120, 90, 90, 90])
                category_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('ALIGN', (0, 1), (0, -1), 'RIGHT'),  # محاذاة يمين للفئات العربية
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # محاذاة وسط للأرقام
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                elements.append(category_table)
                elements.append(Spacer(1, 1*cm))
                
                # إضافة رسم بياني دائري للفئات (إذا كان التقرير مفصلاً)
                if report_type == "detailed":
                    elements.append(PageBreak())
                    elements.append(Paragraph("الرسوم البيانية للفئات المالية", styles['Arabic-Heading']))
                    elements.append(Spacer(1, 0.5*cm))
                    
                    # إنشاء رسم بياني دائري للإيرادات والمصروفات باستخدام matplotlib
                    try:
                        # تجهيز البيانات للرسم البياني
                        categories = list(ai_analysis['category_analysis'].keys())
                        incomes = [ai_analysis['category_analysis'][cat].get('income', 0) for cat in categories]
                        expenses = [ai_analysis['category_analysis'][cat].get('expenses', 0) for cat in categories]
                        
                        # رسم بياني للإيرادات
                        plt.figure(figsize=(8, 6))
                        plt.clf()
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        expenses_data = [e for e in expenses if e > 0]
                        expense_labels = [categories[i] for i in range(len(categories)) if expenses[i] > 0]
                        
                        if expenses_data:
                            ax1.pie(expenses_data, labels=expense_labels, autopct='%1.1f%%', startangle=90)
                            ax1.axis('equal')
                            plt.title('توزيع المصروفات حسب الفئة', fontsize=16)
                            
                            # حفظ الرسم البياني إلى ملف مؤقت
                            expense_chart_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
                            plt.savefig(expense_chart_path, format='png', dpi=150, bbox_inches='tight')
                            plt.close()
                            
                            # إضافة الرسم البياني إلى التقرير
                            elements.append(Image(expense_chart_path, width=400, height=300))
                            elements.append(Spacer(1, 0.5*cm))
                            
                            # حذف الملف المؤقت
                            os.unlink(expense_chart_path)
                        
                        # رسم بياني للإيرادات
                        plt.figure(figsize=(8, 6))
                        plt.clf()
                        fig2, ax2 = plt.subplots(figsize=(8, 6))
                        incomes_data = [i for i in incomes if i > 0]
                        income_labels = [categories[i] for i in range(len(categories)) if incomes[i] > 0]
                        
                        if incomes_data:
                            ax2.pie(incomes_data, labels=income_labels, autopct='%1.1f%%', startangle=90)
                            ax2.axis('equal')
                            plt.title('توزيع الإيرادات حسب الفئة', fontsize=16)
                            
                            # حفظ الرسم البياني إلى ملف مؤقت
                            income_chart_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
                            plt.savefig(income_chart_path, format='png', dpi=150, bbox_inches='tight')
                            plt.close()
                            
                            # إضافة الرسم البياني إلى التقرير
                            elements.append(Image(income_chart_path, width=400, height=300))
                            
                            # حذف الملف المؤقت
                            os.unlink(income_chart_path)
                    except Exception as e:
                        # في حالة فشل إنشاء الرسوم البيانية، إضافة رسالة خطأ
                        elements.append(Paragraph(f"تعذر إنشاء الرسوم البيانية: {str(e)}", styles['Arabic-Body']))
        
        # إضافة تفاصيل المعاملات للتقرير المفصل
        if report_type == "detailed":
            elements.append(PageBreak())
            elements.append(Paragraph("تفاصيل المعاملات المالية", styles['Arabic-Heading']))
            elements.append(Spacer(1, 0.5*cm))
            
            # تحديد الأعمدة التي سيتم عرضها في التقرير
            columns_to_display = []
            
            if 'Date' in data.columns:
                columns_to_display.append('Date')
            if 'Description' in data.columns:
                columns_to_display.append('Description')
            if 'Category' in data.columns:
                columns_to_display.append('Category')
            if 'Income' in data.columns:
                columns_to_display.append('Income')
            if 'Expenses' in data.columns:
                columns_to_display.append('Expenses')
            if 'Net' in data.columns:
                columns_to_display.append('Net')
            
            # ترجمة أسماء الأعمدة إلى العربية
            column_translations = {
                'Date': 'التاريخ',
                'Description': 'الوصف',
                'Category': 'الفئة',
                'Income': 'الإيرادات',
                'Expenses': 'المصروفات',
                'Net': 'الصافي'
            }
            
            # إعداد بيانات الجدول
            table_data = [[column_translations.get(col, col) for col in columns_to_display]]
            
            # تحديد عرض كل عمود
            col_widths = []
            for col in columns_to_display:
                if col == 'Date':
                    col_widths.append(2*cm)
                elif col == 'Description':
                    col_widths.append(6*cm)
                elif col == 'Category':
                    col_widths.append(3*cm)
                else:
                    col_widths.append(2.5*cm)
            
            # إضافة صفوف البيانات (بحد أقصى 50 معاملة للحفاظ على أداء PDF)
            transaction_count = min(len(data), 50)
            for i in range(transaction_count):
                row = data.iloc[i]
                table_row = []
                
                for col in columns_to_display:
                    if col in ['Income', 'Expenses', 'Net'] and pd.notna(row[col]) and row[col] != 0:
                        table_row.append(f"{row[col]:,.2f}")
                    elif col == 'Date' and pd.notna(row[col]):
                        try:
                            date_str = row[col].strftime('%Y-%m-%d')
                            table_row.append(date_str)
                        except:
                            table_row.append(str(row[col]))
                    else:
                        table_row.append(str(row[col]) if pd.notna(row[col]) else "")
                
                table_data.append(table_row)
            
            # إنشاء الجدول
            transactions_table = Table(table_data, colWidths=col_widths)
            
            # تنسيق الجدول
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Arabic' if 'Arabic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
            ]
            
            # تلوين الصفوف بالتناوب
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
            
            # تطبيق التنسيق على الجدول
            transactions_table.setStyle(TableStyle(table_style))
            elements.append(transactions_table)
        
        # إضافة تذييل للتقرير
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph("تم إنشاء هذا التقرير بواسطة محلل البيانات المالية الذكي", styles['Arabic-Body']))
        elements.append(Paragraph(f"تاريخ الإنشاء: {current_date}", styles['Arabic-Body']))
        
        # بناء ملف PDF
        doc.build(elements)
        
        # قراءة محتوى الملف PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # حذف الملف المؤقت
        os.unlink(pdf_path)
        
        # إرجاع المحتوى بالتنسيق المطلوب
        if output_format.lower() == 'pdf':
            return pdf_content
        elif output_format.lower() == 'html':
            # تحويل PDF إلى HTML (ملاحظة: هذا يتطلب مكتبات إضافية)
            return f"<p>تم إنشاء تقرير PDF بنجاح، حجم الملف: {len(pdf_content)} بايت</p>"
        else:
            return pdf_content
        
    except Exception as e:
        # في حالة حدوث خطأ، إرجاع رسالة خطأ
        error_message = f"فشل في إنشاء التقرير: {str(e)}"
        print(error_message)
        return error_message.encode('utf-8') if output_format.lower() == 'pdf' else error_message
