"""
Created as part of ISU C-CHANGE Foresite system on 13 Jan 2020

@author: Matt Nowatzke
@email: mnowatz@iastate.edu
"""
#%%
import pandas as pd
import bdgt_database as db

#%%
class Budget:
    """
    Calculates profitability for rotation, management, and acres.
    """
    #Get basic field info
    def __init__(self, uuid, rotation, current_crop, buac, acres=1, year=2019):
        self.uuid = uuid
        self.rotation = rotation
        self.current_crop = current_crop
        self.buac = buac
        self.acres = acres
        self.expenses = {'fert':0, 'seed':0, 'preharv_mach':0, 'harv_mach':0, 'processing':0, 'chemicals':0, 'extra':0, 'labor':0}
        self.year = year

    def fert_cost(self, n_lbs, phos_lbs, potash_lbs, n_price, phos_price, potash_price):
        """cost of fertilizer per acre
        
        Arguments:
            n_lbs {float} -- pounds of nitrogen applied per acre
            phos_lbs {float} -- pounds of phosphorous applied per acre
            potash_lbs {float} -- pounds of potash/potassium applied per acre
            n_price {float} -- price of nitrogen per pound
            phos_price {float} -- price of phosphorous per pound
            potash_price {float} -- price of potash/potassium per pound
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- total price of fertilizer per acre
        """
        n_cost = (n_lbs * n_price) * self.acres
        phos_cost = (phos_lbs * phos_price) * self.acres
        potash_cost = (potash_lbs * potash_price) * self.acres
        total_fert_cost = n_cost + phos_cost + potash_cost
        self.expenses['fert']=total_fert_cost
        return self.expenses

    def seed_cost(self, seed_rate, seed_price):
        """Calculates cost of seed for one acre
        
        Arguments:
            seed_rate {int} -- number of seeds planted per acre
            seed_price {float} -- cost per 1000 seeds
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- cost of seed per acre
        """
        seed_cost_acre = ((seed_rate * seed_price)/1000) * self.acres
        self.expenses['seed']=seed_cost_acre
        return self.expenses

    def preharvest_machinery_cost(self, fix_chisel, var_chisel, fix_disk, var_disk, fix_applicator, var_applicator, fix_cultivator, var_cultivator, fix_planter, var_planter, fix_sprayer, var_sprayer):
        """Calculates per acre costs for preharvest machinery
        
        Arguments:
            var_chisel {float} -- variable chisel cost
            fix_chisel {float} -- fixed chisel cost
            var_disk {float} -- variable disk cost
            fix_disk {float} -- fixed disk cost
            var_applicator {float} -- variable fertilizer application cost
            fix_applicator {float} -- fixed fertilizer application cost
            var_cultivator {float} -- variable field cultivator cost
            fix_cultivator {float} -- fixed field cultivator cost
            fix_planter {float} -- fixed planter cost
            var_planter {float} -- variable planter cost
            var_sprayer {float} -- variable sprayer cost
            fix_sprayer {float} -- fixed sprayer cost
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- cost of preharvest machinery per acre
        """
        tillage_cost = (var_chisel + fix_chisel + var_disk + fix_disk) * self.acres
        applicator_cost = (var_applicator + fix_applicator) * self.acres
        cultivator_cost = (var_cultivator + fix_cultivator) * self.acres
        planter_cost = (var_planter + fix_planter) * self.acres
        sprayer_cost = (var_sprayer + fix_planter) * self.acres
        total_preharvest = tillage_cost + applicator_cost + cultivator_cost + planter_cost + sprayer_cost
        self.expenses['preharv_mach']=total_preharvest
        return self.expenses

    def harvest_machinery_cost(self, fix_combine, var_combine, fix_wagon, var_wagon):
        """calculates per acre cost of harvest machinery
        
        Arguments:
            fix_combine {float} -- fixed cost of combine/harvester
            var_combine {float} -- variable cost of combine/harvester
            fix_wagon {float} -- fixed cost of wagon/grain cart
            var_wagon {float} -- variable cost of wagon/grain cart
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- total cost per acre of harvest machinery
        """
        combine_cost = (fix_combine + var_combine) * self.acres
        wagon_cost = (fix_wagon + var_wagon) * self.acres
        total_harvest_machinery = combine_cost + wagon_cost
        self.expenses['harv_mach'] = total_harvest_machinery
        return self.expenses

    def processing_cost(self, fix_hauling, var_hauling, fix_drying, var_drying, fix_handling, var_handling):
        """Calculate cost per bushel of processing 
        
        Arguments:
            buac {float} -- bushels of grain per acre
            fix_hauling {float} -- fixed cost of hauling
            var_hauling {float} -- variable cost of hauling
            fix_drying {float} -- fixed cost of drying
            var_drying {float} -- variable cost drying
            fix_handling {float} -- fixed cost of handling
            var_handling {float} -- variable cost of handling
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- total cost of processing per acre
        """
        hauling_cost = ((var_hauling + fix_hauling) * self.buac) * self.acres
        drying_cost = ((var_drying + fix_drying) * self.buac) * self.acres
        handling_cost = ((var_hauling + fix_hauling) * self.buac) * self.acres
        total_processing = hauling_cost + drying_cost + handling_cost
        self.expenses['processing'] = total_processing
        return self.expenses
        
    def chemicals_cost(self, herbicide, insecticide):
        """calculate cost of herbicides and pesticides per acre
        
        Arguments:
            herbicide {float} -- cost per acre of herbicide
            insecticide {float} -- cost per acre of insecticide
            acres {float} -- number of acres in field or area
        
        Returns:
            float -- cost of herbicide and pesticide per acre
        """
        herb_cost = herbicide
        insect_cost = insecticide
        total_chemical = herb_cost + insect_cost
        self.expenses['chemicals'] = total_chemical
        return self.expenses


    def extra_costs(self, crop_insurance, rent_cost, rent=False):
        """calculate cost of extra costs like rent and insurance per acre
        
        Arguments:
            rent {float} -- cost of rent per acre
            crop_insurance {float} -- cost of insurance per acre
            acres {float} -- number of acres to analyze
        
        Returns:
            float -- total extra costs per acre
        """
        if rent == True:
            extra_rent_cost = (rent_cost + crop_insurance) * self.acres
            self.expenses['extra'] = extra_rent_cost
        else:
            extra_own_cost = crop_insurance * self.acres
            self.expenses['extra'] = extra_own_cost
        return self.expenses

    def labor_cost(self, labor_hours, rate_of_pay):
        """calculates cost of labor
        
        Arguments:
            labor_hours {float} -- number of hours of hired labor
            rate_of_pay {float} -- hourly rate of pay in dollars
            acres {float} -- number of acres labor was hired for
        
        Returns:
            float -- total cost of labor per acre
        """
        total_labor = (labor_hours * rate_of_pay) * self.acres
        self.expenses['labor'] = total_labor
        return self.expenses

    def calc_revenue(self, comm_price):
        """calculates total revenue from yield and commodity price
        
        Arguments:
            comm_price {float} -- current price of given commodity
            buac {float} -- yield in bushels per acre
            acres {float} -- number of acres in given field or area
        
        Returns:
            float -- total revenue from given field or area
        """
        calc = (self.buac * self.acres) * comm_price
        self.revenue = round(calc, 2)
        return self.revenue

    #TODO DOCUMENTATION
    def sum_expenses(self):
        """
        Sum total of a list that contains all expenses.
        """
        self.expense_total = sum(self.expenses.values())
        return self.expense_total
        
    def calc_profit(self):
        """[summary]
        
        Arguments:
            revenue {[type]} -- [description]
            expenses {[type]} -- [description]
        
        Keyword Arguments:
            acres {int} -- [description] (default: {1})
        """
        self.profit = self.revenue - self.expense_total
        return self.profit

#%%
def get_mgmt(database, runs_table, mgmt_table, mgmt_id_column):
    """Gets the management data for whichever runs
    
    Arguments:
        database {object} -- connection to the database
        runs_table {str} -- table that contains the run ids
        mgmt_table {str} -- table that contains all the management connected
        to individual runs
        mgmt_id_column {str} -- name of the column that contains the ids
    
    Returns:
        dataframe -- dataframe with all of the management for the specific runs we want
    """
    #TODO Need to remove limit for real deal
    #get the specific runs we want to analyze
    runs_query = f'SELECT * FROM {runs_table} LIMIT 10'
    runs_df = pd.read_sql(runs_query, database)
    #get the column names for the management table to append each run's mgmt
    get_columns_query = f'SELECT * FROM {mgmt_table} LIMIT 0'
    mgmt_df = pd.read_sql(get_columns_query, database)
    for idx, row in runs_df.iterrows():
        mgmt_id = int(row[mgmt_id_column])
        mgmt_query = f'SELECT * FROM {mgmt_table} WHERE {mgmt_id_column}::int4 = {mgmt_id}'
        mgmt_df = mgmt_df.append(pd.read_sql(mgmt_query, database), ignore_index=True)
    #return dataframe with all the management for our specific runs
    return mgmt_df



#%%
#specify year for data and get costs of production
dbconn = db.connect_to_db('database.ini')
mgmt_df = get_mgmt(dbconn, 'public.runs_samples', 'public.mgmt_samples', 'management_sample_id')

#%%
#placeholders
buac = 180
phos = 40
potash = 30
year = 2020
corn_price = 3.71
soybean_price = 8.36

#%%
#clean the rotations to match
mgmt_df['fertilizer.rotation'][(mgmt_df['fertilizer.rotation'] == 'cont-maize')] = 'cc'
mgmt_df['fertilizer.rotation'][(mgmt_df['fertilizer.rotation'] == 'maize-soybean') & (mgmt_df['crops.sow_crop'] == 'maize')] = 'cfs'
mgmt_df['fertilizer.rotation'][(mgmt_df['fertilizer.rotation'] == 'maize-soybean') & (mgmt_df['crops.sow_crop'] == 'soybean')] = 'sfc'

#%%
#get the production costs for a given year
costs_query = f'SELECT * FROM sandbox.crop_prod_costs WHERE year = \'{year}\''    
prod_costs_df = pd.read_sql(costs_query, dbconn)

#%%
columns = [
    'management_sample_id',
    'fertilizer',
    'seed',
    'preharv_machinery',
    'harvest_machinery',
    'processing',
    'chemicals',
    'extra',
    'labor',
    'revenue',
    'expenses',
    'profit'
    ]
output_df = pd.DataFrame(columns=columns)


def analyze_budgets(df):
    for i in mgmt_df.index:
        val = df.get_value
#%%
#create new instance of Budget class
for idx, row in mgmt_df.iterrows():
    run_id = row['management_sample_id']
    rotation = row['fertilizer.rotation']
    current_crop = row['crops.sow_crop']
    n_lbs = row['fertilizer.app1_kg_n_ha'] + row['fertilizer.app2_kg_n_ha']
    phos_lbs = 40
    potash_lbs = 30
    n_price = float(prod_costs_df['fixed-cost'][(prod_costs_df['input'] == 'nitrogen') & (prod_costs_df['rotation'] == rotation)])
    phos_price = float(prod_costs_df['fixed-cost'][(prod_costs_df['input'] == 'phosphorous') & (prod_costs_df['rotation'] == rotation)])
    potash_price = float(prod_costs_df['fixed-cost'][(prod_costs_df['input'] == 'potash') & (prod_costs_df['rotation'] == rotation)])
    mgmt_run = Budget(run_id, rotation, current_crop, buac, acres=100, year=2020)
    output_df = output_df['fertilizer'].append(mgmt_run.fert_cost(n_lbs, phos_lbs, potash_lbs, n_price, phos_price, potash_price), ignore_index=True)


# def main():
#     maize=Budget("cfs", "maize", 200, 100)
#     maize.fert_cost(180, 40, 30, .38, .41, .31)
#     maize.seed_cost(30000, 3.19)
#     maize.preharvest_machinery_cost(3.9, 3.6, 4.6, 3.4, 4.3, 4.4, 2.7, 2.6, 4.8, 5.9, 2.0, 2.2)
#     maize.harvest_machinery_cost(13.10, 6.7, 6.3, 3.0)
#     maize.processing_cost(0.044, 0.038, 0.05, 0.17, 0.02, 0.02)
#     maize.chemicals_cost(48.36, 15.16)
#     maize.extra_costs(9.5, 219, rent=True)
#     maize.labor_cost(2, 14.25)
    #print(maize.calc_revenue(3.71))
    #print(maize.sum_expenses())
    #print(maize.calc_profit())
    #print(maize.expenses)
    
#%%
if __name__ == "__main__":
    main()
