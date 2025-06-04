import streamlit as st
import datetime
from datetime import timedelta
import os
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

class PersonalFinanceForecaster:
    def __init__(self):
        self.balance_file = "finance_balance.json"
        
        # Load saved balance or start with 0
        self.current_balance = self.load_balance()
        self.daily_expenses = 100.0
        
        # Monthly recurring expenses from Excel file
        self.monthly_expenses = {
            1: [("Davis Schools Lunch", 20.00)],
            2: [("Kindle", 13.93), ("Audible", 16.03), ("Harp", 150.00), ("Kohls", 100.00), ("Grass Roots Coop", 158.76)],
            4: [("Kindle", 12.86), ("Paypal Instant", 36.24)],
            5: [("Mint mobile", 130.00)],
            6: [("T-MOBILE Handset", 83.37), ("South Davis Rec", 40.00)],
            8: [("Mint mobile", 130.76)],
            12: [("JSB Guitar", 35.00), ("Mortgage", 930.00)],
            13: [("Internet", 61.10)],
            15: [("Netflix", 20.00), ("Claude", 22.00)],
            18: [("Phone Rob", 124.64)],
            19: [("ChatGPT", 20.00), ("CAP 1 Mike", 110.00), ("Sewer", 75.00)],
            20: [("Foundation Furnace", 110.00)],
            21: [("Cap 1 Rob", 220.00), ("Merinda Harp", 50.00)],
            22: [("Allstate Car insurance", 322.88), ("T-Mobile", 113.00)],
            23: [("Psych", 25.00)],
            25: [("Car Payment", 420.00)],
            27: [("Ryan xfer", 300.00), ("Gas", 30.00), ("NYTimes", 25.00), ("Psych", 25.00), ("Paypal", 30.00)],
            28: [("Paypal", 13.00)],
            29: [("Orthodontics", 119.00), ("Paypal 2", 26.95), ("Dominion", 74.00)],
            30: [("Rose", 25.00), ("Paypal 2", 26.95)]
        }
        
        self.bi_weekly_pay = 2700.0
        self.social_security = 2600.0

    def load_balance(self):
        """Load the saved balance from file"""
        try:
            if os.path.exists(self.balance_file):
                with open(self.balance_file, 'r') as f:
                    data = json.load(f)
                    balance = data.get('current_balance', 0.0)
                    return balance
            else:
                return 0.0
        except Exception as e:
            st.error(f"Error loading balance: {e}")
            return 0.0

    def save_balance(self):
        """Save the current balance to file"""
        try:
            data = {
                'current_balance': self.current_balance,
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.balance_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving balance: {e}")

    def set_current_balance(self, balance):
        """Update the current balance and save it"""
        self.current_balance = float(balance)
        self.save_balance()

    def update_balance(self, amount, description="Balance adjustment"):
        """Add or subtract an amount from the current balance"""
        self.current_balance += amount
        self.save_balance()
        return f"{description}: {amount:+.2f}"

    def find_fourth_wednesday(self, year, month):
        """Find the 4th Wednesday of a given month"""
        first_day = datetime.date(year, month, 1)
        days_to_first_wed = (2 - first_day.weekday()) % 7
        first_wednesday = first_day + timedelta(days=days_to_first_wed)
        fourth_wednesday = first_wednesday + timedelta(weeks=3)
        
        if fourth_wednesday.month == month:
            return fourth_wednesday
        else:
            return first_wednesday + timedelta(weeks=2)

    def get_bi_weekly_pay_dates(self, start_date, num_days):
        """Get all bi-weekly pay dates starting June 13, 2025"""
        pay_dates = []
        first_pay_date = datetime.date(2025, 6, 13)
        end_date = start_date + timedelta(days=num_days)
        
        current_pay_date = first_pay_date
        if start_date > first_pay_date:
            weeks_since = (start_date - first_pay_date).days // 7
            cycles_passed = weeks_since // 2
            current_pay_date = first_pay_date + timedelta(weeks=(cycles_passed + 1) * 2)
        
        while current_pay_date <= end_date:
            if current_pay_date >= start_date:
                pay_dates.append(current_pay_date)
            current_pay_date += timedelta(weeks=2)
        
        return pay_dates

    def get_social_security_dates(self, start_date, num_days):
        """Get all Social Security payment dates (4th Wednesday)"""
        ss_dates = []
        end_date = start_date + timedelta(days=num_days)
        
        current_year = max(2025, start_date.year)
        current_month = 6 if current_year == 2025 and start_date.month < 6 else start_date.month
        
        for _ in range(6):
            if current_year > end_date.year or (current_year == end_date.year and current_month > end_date.month):
                break
                
            fourth_wed = self.find_fourth_wednesday(current_year, current_month)
            if start_date <= fourth_wed <= end_date:
                ss_dates.append(fourth_wed)
            
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        return ss_dates

    def generate_forecast_data(self, num_days=20):
        """Generate forecast data and return it for display"""
        start_date = datetime.date.today()
        running_balance = self.current_balance
        
        # Get all scheduled transactions
        pay_dates = self.get_bi_weekly_pay_dates(start_date, num_days)
        ss_dates = self.get_social_security_dates(start_date, num_days)
        
        forecast_data = []
        dates = []
        balances = []
        daily_changes = []
        
        for i in range(num_days + 1):
            if i == 0:
                dates.append(start_date)
                balances.append(running_balance)
                daily_changes.append(0)
            else:
                current_date = start_date + timedelta(days=i-1)
                daily_change = 0
                transactions = []
                
                # Daily expenses
                daily_change -= self.daily_expenses
                transactions.append(f"Daily expenses: -${self.daily_expenses:.2f}")
                
                # Check for bi-weekly pay
                if current_date in pay_dates:
                    daily_change += self.bi_weekly_pay
                    transactions.append(f"Bi-weekly pay: +${self.bi_weekly_pay:.2f}")
                
                # Check for Social Security
                if current_date in ss_dates:
                    daily_change += self.social_security
                    transactions.append(f"Social Security: +${self.social_security:.2f}")
                
                # Check for monthly expenses
                day_of_month = current_date.day
                if day_of_month in self.monthly_expenses:
                    for desc, amount in self.monthly_expenses[day_of_month]:
                        daily_change -= amount
                        transactions.append(f"{desc}: -${amount:.2f}")
                
                running_balance += daily_change
                
                forecast_data.append({
                    'Date': current_date,
                    'Day': current_date.strftime('%A'),
                    'Transactions': '; '.join(transactions),
                    'Daily Change': daily_change,
                    'Balance': running_balance
                })
                
                dates.append(current_date)
                balances.append(running_balance)
                daily_changes.append(daily_change)
        
        return forecast_data, dates, balances, daily_changes, pay_dates, ss_dates

    def create_cash_flow_plot(self, num_days=20):
        """Create matplotlib figure for cash flow"""
        start_date = datetime.date.today()
        running_balance = self.current_balance
        
        dates = []
        balances = []
        daily_changes = []
        
        pay_dates = self.get_bi_weekly_pay_dates(start_date, num_days)
        ss_dates = self.get_social_security_dates(start_date, num_days)
        major_expense_days = []
        
        for i in range(num_days + 1):
            if i == 0:
                dates.append(start_date)
                balances.append(running_balance)
                daily_changes.append(0)
            else:
                current_date = start_date + timedelta(days=i-1)
                daily_change = 0
                
                # Daily expenses
                daily_change -= self.daily_expenses
                
                # Check for bi-weekly pay
                if current_date in pay_dates:
                    daily_change += self.bi_weekly_pay
                
                # Check for Social Security
                if current_date in ss_dates:
                    daily_change += self.social_security
                
                # Check for monthly expenses
                day_of_month = current_date.day
                daily_expense_total = 0
                if day_of_month in self.monthly_expenses:
                    for desc, amount in self.monthly_expenses[day_of_month]:
                        daily_change -= amount
                        daily_expense_total += amount
                
                if daily_expense_total > 300:
                    major_expense_days.append(current_date)
                
                running_balance += daily_change
                dates.append(current_date)
                balances.append(running_balance)
                daily_changes.append(daily_change)
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Personal Finance Cash Flow Forecast', fontsize=16, fontweight='bold')
        
        # Top plot: Running Balance
        ax1.plot(dates, balances, linewidth=3, color='darkblue', marker='o', markersize=4)
        
        # Color negative balance areas red
        for i in range(len(dates)):
            if balances[i] < 0 and i > 0:
                ax1.axvspan(dates[i-1], dates[i], alpha=0.3, color='red')
        
        # Add horizontal line at zero
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
        
        # Mark special days
        for pay_day in pay_dates:
            if pay_day in dates:
                idx = dates.index(pay_day)
                ax1.scatter(pay_day, balances[idx], color='green', s=100, marker='^', 
                           label='Payday' if pay_day == pay_dates[0] else "", zorder=5)
        
        for ss_day in ss_dates:
            if ss_day in dates:
                idx = dates.index(ss_day)
                ax1.scatter(ss_day, balances[idx], color='blue', s=100, marker='s', 
                           label='Social Security' if ss_day == ss_dates[0] else "", zorder=5)
        
        for expense_day in major_expense_days:
            if expense_day in dates:
                idx = dates.index(expense_day)
                ax1.scatter(expense_day, balances[idx], color='orange', s=100, marker='v', 
                           label='Major Expenses' if expense_day == major_expense_days[0] else "", zorder=5)
        
        ax1.set_title('Cash Balance Over Time', fontsize=14)
        ax1.set_ylabel('Balance ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Bottom plot: Daily Changes
        colors = ['green' if x >= 0 else 'red' for x in daily_changes[1:]]
        ax2.bar(dates[1:], daily_changes[1:], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        ax2.set_title('Daily Cash Flow Changes', fontsize=14)
        ax2.set_ylabel('Daily Change ($)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Format x-axis dates
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add statistics
        min_balance = min(balances)
        max_balance = max(balances)
        final_balance = balances[-1]
        days_negative = sum(1 for b in balances if b < 0)
        
        stats_text = f'''Statistics:
Starting: ${balances[0]:,.0f}
Ending: ${final_balance:,.0f}
Minimum: ${min_balance:,.0f}
Maximum: ${max_balance:,.0f}
Days Negative: {days_negative}'''
        
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return fig, min_balance, days_negative

    def get_monthly_expenses_summary(self):
        """Get summary of monthly expenses"""
        expenses_summary = []
        total_monthly = 0
        
        for day in sorted(self.monthly_expenses.keys()):
            day_total = 0
            day_expenses = []
            for desc, amount in self.monthly_expenses[day]:
                day_expenses.append({'Description': desc, 'Amount': amount})
                day_total += amount
                total_monthly += amount
            
            expenses_summary.append({
                'Day': day,
                'Expenses': day_expenses,
                'Day Total': day_total
            })
        
        return expenses_summary, total_monthly

# Initialize the forecaster
if 'forecaster' not in st.session_state:
    st.session_state.forecaster = PersonalFinanceForecaster()

def main():
    st.set_page_config(
        page_title="Personal Finance Forecaster",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 Personal Finance Cash Flow Forecaster")
    st.markdown("---")
    
    forecaster = st.session_state.forecaster
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Current balance display and update
        st.subheader("Current Balance")
        st.metric("Balance", f"${forecaster.current_balance:,.2f}")
        
        new_balance = st.number_input(
            "Update Balance",
            value=forecaster.current_balance,
            step=100.0,
            format="%.2f"
        )
        
        if st.button("💾 Save Balance"):
            forecaster.set_current_balance(new_balance)
            st.success(f"Balance updated to ${new_balance:,.2f}")
            st.rerun()
        
        st.markdown("---")
        
        # Quick adjustment
        st.subheader("Quick Adjustment")
        adjustment_amount = st.number_input(
            "Amount (+/-)",
            value=0.0,
            step=50.0,
            format="%.2f"
        )
        adjustment_desc = st.text_input("Description", "Manual adjustment")
        
        if st.button("➕➖ Apply Adjustment"):
            if adjustment_amount != 0:
                message = forecaster.update_balance(adjustment_amount, adjustment_desc)
                st.success(message)
                st.rerun()
        
        st.markdown("---")
        
        # Daily expenses
        st.subheader("Daily Expenses")
        new_daily_expenses = st.number_input(
            "Daily Expenses Amount",
            value=forecaster.daily_expenses,
            min_value=0.0,
            step=10.0,
            format="%.2f"
        )
        
        if st.button("💸 Update Daily Expenses"):
            forecaster.daily_expenses = new_daily_expenses
            st.success(f"Daily expenses updated to ${new_daily_expenses:.2f}")
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Forecast", "📈 Cash Flow Chart", "📋 Monthly Expenses", "ℹ️ About"])
    
    with tab1:
        st.header("📊 Cash Flow Forecast")
        
        # Forecast period selector
        col1, col2 = st.columns([1, 3])
        with col1:
            forecast_days = st.selectbox("Forecast Period", [7, 14, 20, 30], index=2)
        
        # Generate forecast
        forecast_data, dates, balances, daily_changes, pay_dates, ss_dates = forecaster.generate_forecast_data(forecast_days)
        
        # Summary metrics
        if forecast_data:
            final_balance = forecast_data[-1]['Balance']
            total_change = final_balance - forecaster.current_balance
            min_balance = min([d['Balance'] for d in forecast_data])
            days_negative = sum(1 for d in forecast_data if d['Balance'] < 0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Starting Balance", f"${forecaster.current_balance:,.2f}")
            with col2:
                st.metric("Ending Balance", f"${final_balance:,.2f}", f"${total_change:+,.2f}")
            with col3:
                st.metric("Minimum Balance", f"${min_balance:,.2f}")
            with col4:
                st.metric("Days Negative", days_negative)
            
            # Warnings
            if min_balance < 0:
                st.error(f"⚠️ WARNING: Balance goes negative! Lowest point: ${min_balance:,.2f}")
            elif final_balance < 500:
                st.warning("⚠️ CAUTION: Low balance projected")
            else:
                st.success("✅ Balance looks healthy")
            
            # Forecast table
            st.subheader("Daily Breakdown")
            df = pd.DataFrame(forecast_data)
            df['Date'] = df['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
            df['Daily Change'] = df['Daily Change'].apply(lambda x: f"${x:+,.2f}")
            df['Balance'] = df['Balance'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.header("📈 Cash Flow Chart")
        
        chart_days = st.selectbox("Chart Period (Days)", [7, 14, 20, 30], index=2, key="chart_days")
        
        if st.button("🔄 Generate Chart"):
            with st.spinner("Generating cash flow chart..."):
                fig, min_balance, days_negative = forecaster.create_cash_flow_plot(chart_days)
                st.pyplot(fig)
                
                if min_balance < 0:
                    st.error(f"⚠️ Chart shows negative balance! Minimum: ${min_balance:,.2f}")
    
    with tab3:
        st.header("📋 Monthly Recurring Expenses")
        
        expenses_summary, total_monthly = forecaster.get_monthly_expenses_summary()
        
        st.metric("Total Monthly Expenses", f"${total_monthly:,.2f}")
        
        # Create expenses dataframe
        expense_data = []
        for day_info in expenses_summary:
            for expense in day_info['Expenses']:
                expense_data.append({
                    'Day of Month': day_info['Day'],
                    'Description': expense['Description'],
                    'Amount': f"${expense['Amount']:.2f}"
                })
        
        if expense_data:
            df_expenses = pd.DataFrame(expense_data)
            st.dataframe(df_expenses, use_container_width=True)
        
        # Group by day
        st.subheader("Expenses by Day")
        for day_info in expenses_summary:
            with st.expander(f"Day {day_info['Day']} - Total: ${day_info['Day Total']:.2f}"):
                for expense in day_info['Expenses']:
                    st.write(f"• {expense['Description']}: ${expense['Amount']:.2f}")
    
    with tab4:
        st.header("ℹ️ About This App")
        
        st.markdown("""
        ### Personal Finance Cash Flow Forecaster
        
        This application helps you forecast your personal cash flow based on:
        
        **Income Sources:**
        - Bi-weekly paychecks (${:,.2f})
        - Social Security payments (${:,.2f}) on 4th Wednesday of each month
        
        **Expenses:**
        - Daily expenses (${:.2f} per day)
        - Monthly recurring expenses on specific days
        
        **Features:**
        - 📊 Detailed daily forecast with transaction breakdown
        - 📈 Visual cash flow charts showing balance trends
        - 📋 Complete list of monthly recurring expenses
        - 💾 Automatic balance saving between sessions
        - ⚠️ Warnings for negative balance periods
        
        **How to Use:**
        1. Set your current balance in the sidebar
        2. Adjust daily expenses if needed
        3. View forecasts in the Forecast tab
        4. Generate visual charts in the Cash Flow Chart tab
        5. Review monthly expenses in the Monthly Expenses tab
        
        The app automatically saves your balance and settings between sessions.
        """.format(forecaster.bi_weekly_pay, forecaster.social_security, forecaster.daily_expenses))

if __name__ == "__main__":
    main()