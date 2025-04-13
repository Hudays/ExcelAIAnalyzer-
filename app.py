import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime
import os
import tempfile
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from utilities import (
    analyze_excel_data,
    generate_professional_report,
    generate_ai_insights,
    generate_financial_predictions,
    detect_excel_structure,
    classify_transactions
)

# تحميل متغيرات البيئة
load_dotenv()

# إعداد الصفحة
st.set_page_config(
    page_title="محلل البيانات المالية الذكي",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحميل CSS
with open(os.path.join(os.path.dirname(__file__), "styles.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# تهيئة متغيرات الجلسة
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("DEEPSEEK_API_KEY", "")
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'predictions' not in st.session_state:
    st.session_state.predictions = None

def main():
    """التطبيق الرئيسي"""
    
    # شريط التنقل الجانبي
    with st.sidebar:
        st.title("محلل البيانات المالية الذكي")
        st.image("https://img.icons8.com/color/96/000000/economic-improvement.png", width=100)
        
        # قسم إعدادات API
        st.subheader("إعدادات API")
        api_key = st.text_input(
            "DeepSeek API Key",
            value=st.session_state.api_key,
            type="password",
            help="أدخل مفتاح DeepSeek API لاستخدام ميزات التحليل الذكي"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            os.environ["DEEPSEEK_API_KEY"] = api_key
        
        # زر تنزيل نموذج الإكسل
        with open(os.path.join(os.path.dirname(__file__), "template.xlsx"), "rb") as template_file:
            template_bytes = template_file.read()
            st.download_button(
                label="تنزيل قالب الإكسل",
                data=template_bytes,
                file_name="financial_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # اقتباس تحفيزي
        st.markdown("---")
        st.markdown(
            "> الذكاء المالي يساعدك على اتخاذ قرارات ذكية وتحسين مستقبلك المالي"
        )
    
    # عنوان الصفحة الرئيسية
    st.title("محلل البيانات المالية الذكي")
    st.markdown(
        """
        منصة تعتمد على الذكاء الاصطناعي لتحليل بياناتك المالية وإنشاء تقارير احترافية
        """
    )
    
    # علامات التبويب الرئيسية
    tabs = st.tabs([
        "استيراد البيانات 📤", 
        "التحليل الذكي 🧠", 
        "الرسوم البيانية 📊", 
        "التقارير 📝", 
        "التنبؤات المالية 🔮"
    ])
    
    # تبويب استيراد البيانات
    with tabs[0]:
        st.header("استيراد بياناتك المالية")
        
        # مربع سحب وإفلات لرفع الملف
        uploaded_file = st.file_uploader(
            "قم برفع ملف إكسل يحتوي على بياناتك المالية",
            type=["xlsx", "xls"],
            help="يجب أن يحتوي ملف الإكسل على أعمدة تتضمن التاريخ، الوصف، الفئة، الإيرادات، والمصروفات"
        )
        
        if uploaded_file:
            try:
                # قراءة البيانات
                df = pd.read_excel(uploaded_file)
                st.session_state.data = df
                
                # اكتشاف بنية الملف
                col_mapping = detect_excel_structure(df)
                
                if not col_mapping:
                    st.error("لم يتم التعرف على بنية الملف. تأكد من استخدام الأعمدة المطلوبة.")
                else:
                    # عرض معاينة البيانات الخام
                    with st.expander("معاينة البيانات الخام"):
                        st.dataframe(df.head(10))
                    
                    # معالجة البيانات
                    if st.button("تحليل البيانات", use_container_width=True):
                        with st.spinner("جاري تحليل البيانات..."):
                            processed_data = analyze_excel_data(df, col_mapping)
                            st.session_state.processed_data = processed_data
                            
                            # إعادة ضبط نتائج التحليل السابقة
                            st.session_state.analysis_results = None
                            st.session_state.predictions = None
                            
                            st.success("تم تحليل البيانات بنجاح!")
                            
                            # عرض معاينة البيانات المعالجة
                            st.subheader("البيانات المعالجة")
                            st.dataframe(processed_data)
                            
                            # أزرار التصدير
                            col1, col2 = st.columns(2)
                            with col1:
                                csv = processed_data.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="تنزيل كملف CSV",
                                    data=csv,
                                    file_name=f"financial_data_{datetime.now().strftime('%Y%m%d')}.csv",
                                    mime="text/csv"
                                )
                            with col2:
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    processed_data.to_excel(writer, index=False)
                                excel_data = output.getvalue()
                                st.download_button(
                                    label="تنزيل كملف Excel",
                                    data=excel_data,
                                    file_name=f"financial_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
            
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {str(e)}")
    
    # تبويب التحليل الذكي
    with tabs[1]:
        st.header("التحليل المالي الذكي")
        
        if st.session_state.processed_data is None:
            st.info("قم باستيراد وتحليل بياناتك أولاً")
        else:
            # التحقق من وجود مفتاح API
            if not st.session_state.api_key:
                st.warning("أدخل مفتاح DeepSeek API في الإعدادات للاستفادة من ميزات التحليل الذكي")
            else:
                # زر إجراء التحليل الذكي
                if st.session_state.analysis_results is None:
                    if st.button("إجراء تحليل ذكي للبيانات", use_container_width=True):
                        with st.spinner("جاري تحليل البيانات باستخدام الذكاء الاصطناعي..."):
                            try:
                                analysis_results = generate_ai_insights(st.session_state.processed_data)
                                st.session_state.analysis_results = analysis_results
                                st.success("تم إكمال التحليل الذكي!")
                            except Exception as e:
                                st.error(f"حدث خطأ في التحليل الذكي: {str(e)}")
                
                # عرض نتائج التحليل
                if st.session_state.analysis_results:
                    # عرض ملخص التحليل
                    st.subheader("ملخص التحليل المالي")
                    st.markdown(st.session_state.analysis_results.get("summary", ""))
                    
                    # عرض الرؤى والتوصيات
                    st.subheader("الرؤى والتوصيات")
                    insights = st.session_state.analysis_results.get("insights", [])
                    for i, insight in enumerate(insights, 1):
                        st.markdown(f"**{i}.** {insight}")
                    
                    # عرض الفئات والتصنيفات
                    st.subheader("تحليل الفئات")
                    categories = st.session_state.analysis_results.get("category_analysis", {})
                    if categories:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### فئات الإيرادات")
                            for cat, amount in categories.get("income", {}).items():
                                st.markdown(f"**{cat}**: {amount:,.2f}")
                        with col2:
                            st.markdown("#### فئات المصروفات")
                            for cat, amount in categories.get("expenses", {}).items():
                                st.markdown(f"**{cat}**: {amount:,.2f}")
    
    # تبويب الرسوم البيانية
    with tabs[2]:
        st.header("الرسوم البيانية")
        
        if st.session_state.processed_data is None:
            st.info("قم باستيراد وتحليل بياناتك أولاً")
        else:
            data = st.session_state.processed_data
            
            # الإجماليات
            total_income = data['Income'].sum() if 'Income' in data.columns else 0
            total_expenses = data['Expenses'].sum() if 'Expenses' in data.columns else 0
            
            # عرض الإجماليات
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("إجمالي الإيرادات", f"{total_income:,.2f}")
            with col2:
                st.metric("إجمالي المصروفات", f"{total_expenses:,.2f}")
            with col3:
                st.metric("صافي الدخل", f"{total_income - total_expenses:,.2f}")
            
            # صف للرسوم البيانية
            st.subheader("توزيع الإيرادات والمصروفات")
            col1, col2 = st.columns(2)
            
            with col1:
                # مخطط دائري للإيرادات حسب الفئة
                if 'Category' in data.columns and 'Income' in data.columns:
                    income_by_category = data[data['Income'] > 0].groupby('Category')['Income'].sum().reset_index()
                    
                    if not income_by_category.empty:
                        fig = px.pie(
                            income_by_category, 
                            values='Income', 
                            names='Category',
                            title='توزيع الإيرادات حسب الفئة',
                            color_discrete_sequence=px.colors.sequential.Greens
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("لا توجد بيانات إيرادات لعرضها")
            
            with col2:
                # مخطط دائري للمصروفات حسب الفئة
                if 'Category' in data.columns and 'Expenses' in data.columns:
                    expenses_by_category = data[data['Expenses'] > 0].groupby('Category')['Expenses'].sum().reset_index()
                    
                    if not expenses_by_category.empty:
                        fig = px.pie(
                            expenses_by_category, 
                            values='Expenses', 
                            names='Category',
                            title='توزيع المصروفات حسب الفئة',
                            color_discrete_sequence=px.colors.sequential.Reds
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("لا توجد بيانات مصروفات لعرضها")
            
            # تحليل زمني
            st.subheader("التحليل الزمني")
            
            if 'Date' in data.columns:
                # تحويل التاريخ إلى نوع تاريخ
                data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
                
                # تجميع البيانات حسب الشهر
                if not data['Date'].isna().all():
                    monthly_data = data.groupby(pd.Grouper(key='Date', freq='M')).agg({
                        'Income': 'sum',
                        'Expenses': 'sum'
                    }).reset_index()
                    
                    # حساب صافي الدخل
                    monthly_data['Net'] = monthly_data['Income'] - monthly_data['Expenses']
                    
                    # رسم المخطط الزمني
                    fig = go.Figure()
                    
                    # إضافة الإيرادات
                    fig.add_trace(go.Scatter(
                        x=monthly_data['Date'],
                        y=monthly_data['Income'],
                        mode='lines+markers',
                        name='الإيرادات',
                        line=dict(color='green', width=2)
                    ))
                    
                    # إضافة المصروفات
                    fig.add_trace(go.Scatter(
                        x=monthly_data['Date'],
                        y=monthly_data['Expenses'],
                        mode='lines+markers',
                        name='المصروفات',
                        line=dict(color='red', width=2)
                    ))
                    
                    # إضافة صافي الدخل
                    fig.add_trace(go.Scatter(
                        x=monthly_data['Date'],
                        y=monthly_data['Net'],
                        mode='lines+markers',
                        name='صافي الدخل',
                        line=dict(color='blue', width=2)
                    ))
                    
                    # تحديث التخطيط
                    fig.update_layout(
                        title='التدفق المالي الشهري',
                        xaxis_title='الشهر',
                        yaxis_title='المبلغ',
                        hovermode='x unified',
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("لم يتم التعرف على صيغة التاريخ بشكل صحيح")
            else:
                st.warning("عمود التاريخ غير موجود لعرض التحليل الزمني")
    
    # تبويب التقارير
    with tabs[3]:
        st.header("التقارير المالية")
        
        if st.session_state.processed_data is None:
            st.info("قم باستيراد وتحليل بياناتك أولاً")
        else:
            # اختيار نوع التقرير
            report_type = st.radio(
                "اختر نوع التقرير",
                ["تقرير ملخص", "تقرير مفصل"],
                horizontal=True
            )
            
            # خيار استخدام التحليل الذكي
            use_ai = st.checkbox(
                "تضمين التحليل الذكي في التقرير", 
                value=True,
                help="يتطلب وجود نتائج تحليل ذكي"
            )
            
            # خيار تضمين الرسوم البيانية
            include_charts = st.checkbox(
                "تضمين الرسوم البيانية في التقرير",
                value=True
            )
            
            # إنشاء التقرير
            if st.button("إنشاء التقرير", use_container_width=True):
                with st.spinner("جاري إنشاء التقرير..."):
                    try:
                        # التحقق من وجود تحليل ذكي إذا تم اختياره
                        ai_analysis = None
                        if use_ai and not st.session_state.analysis_results:
                            if st.session_state.api_key:
                                ai_analysis = generate_ai_insights(st.session_state.processed_data)
                                st.session_state.analysis_results = ai_analysis
                            else:
                                st.warning("لا يمكن استخدام التحليل الذكي بدون مفتاح API")
                        elif use_ai:
                            ai_analysis = st.session_state.analysis_results
                        
                        # تحديد نوع التقرير
                        report_type_value = "summary" if report_type == "تقرير ملخص" else "detailed"
                        
                        # إنشاء التقرير
                        pdf_content = generate_professional_report(
                            data=st.session_state.processed_data,
                            ai_analysis=ai_analysis,
                            report_type=report_type_value,
                            output_format="pdf"
                        )
                        
                        # تنزيل التقرير
                        st.download_button(
                            label="تنزيل التقرير (PDF)",
                            data=pdf_content,
                            file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                        
                        st.success("تم إنشاء التقرير بنجاح!")
                    
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إنشاء التقرير: {str(e)}")
    
    # تبويب التنبؤات المالية
    with tabs[4]:
        st.header("التنبؤات المالية")
        
        if st.session_state.processed_data is None:
            st.info("قم باستيراد وتحليل بياناتك أولاً")
        else:
            # التحقق من وجود مفتاح API
            if not st.session_state.api_key:
                st.warning("أدخل مفتاح DeepSeek API في الإعدادات للاستفادة من ميزات التنبؤ المالي")
            else:
                # إعدادات التنبؤ
                st.subheader("إعدادات التنبؤ")
                
                col1, col2 = st.columns(2)
                with col1:
                    months_ahead = st.slider(
                        "عدد الأشهر المستقبلية للتنبؤ",
                        min_value=1,
                        max_value=12,
                        value=3
                    )
                
                # زر إنشاء التنبؤات
                if st.session_state.predictions is None:
                    if st.button("إنشاء تنبؤات مالية", use_container_width=True):
                        # التحقق من وجود بيانات تاريخية
                        if 'Date' not in st.session_state.processed_data.columns:
                            st.error("البيانات لا تحتوي على عمود التاريخ المطلوب للتنبؤ")
                        else:
                            with st.spinner("جاري إنشاء التنبؤات المالية..."):
                                try:
                                    predictions = generate_financial_predictions(
                                        st.session_state.processed_data,
                                        months_ahead
                                    )
                                    
                                    st.session_state.predictions = predictions
                                    st.success("تم إنشاء التنبؤات بنجاح!")
                                
                                except Exception as e:
                                    st.error(f"حدث خطأ في إنشاء التنبؤات: {str(e)}")
                
                # عرض التنبؤات
                if st.session_state.predictions:
                    # عرض ملخص التنبؤات
                    st.subheader("ملخص التنبؤات المالية")
                    st.markdown(st.session_state.predictions.get("summary", ""))
                    
                    # عرض التنبؤات الشهرية
                    st.subheader("التنبؤات الشهرية")
                    
                    monthly_predictions = st.session_state.predictions.get("monthly_predictions", [])
                    if monthly_predictions:
                        # إنشاء DataFrame من التنبؤات
                        predictions_df = pd.DataFrame(monthly_predictions)
                        
                        # عرض جدول التنبؤات
                        st.dataframe(predictions_df)
                        
                        # رسم مخطط التنبؤات
                        fig = go.Figure()
                        
                        # إضافة الإيرادات المتوقعة
                        fig.add_trace(go.Scatter(
                            x=predictions_df['month'],
                            y=predictions_df['predicted_income'],
                            mode='lines+markers',
                            name='الإيرادات المتوقعة',
                            line=dict(color='green', width=2)
                        ))
                        
                        # إضافة المصروفات المتوقعة
                        fig.add_trace(go.Scatter(
                            x=predictions_df['month'],
                            y=predictions_df['predicted_expenses'],
                            mode='lines+markers',
                            name='المصروفات المتوقعة',
                            line=dict(color='red', width=2)
                        ))
                        
                        # إضافة صافي الدخل المتوقع
                        fig.add_trace(go.Scatter(
                            x=predictions_df['month'],
                            y=predictions_df['predicted_net'],
                            mode='lines+markers',
                            name='صافي الدخل المتوقع',
                            line=dict(color='blue', width=2)
                        ))
                        
                        # تحديث التخطيط
                        fig.update_layout(
                            title='التنبؤات المالية المستقبلية',
                            xaxis_title='الشهر',
                            yaxis_title='المبلغ المتوقع',
                            hovermode='x unified',
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # تصدير التنبؤات
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = predictions_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="تنزيل التنبؤات (CSV)",
                                data=csv,
                                file_name=f"financial_predictions_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        
                        with col2:
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                predictions_df.to_excel(writer, index=False)
                            excel_data = output.getvalue()
                            st.download_button(
                                label="تنزيل التنبؤات (Excel)",
                                data=excel_data,
                                file_name=f"financial_predictions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.info("لم يتم إنشاء تنبؤات شهرية")
    
    # القدم
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center;">
            محلل البيانات المالية الذكي - جميع الحقوق محفوظة &copy; {0}
        </div>
        """.format(datetime.now().year),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
