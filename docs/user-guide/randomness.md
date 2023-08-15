# Simulation Randomness

## Demand Generation K-Factors {k-factors}

There are multiple sources of variability that is introduced in the simulation.  
Variability in the level of demand by passenger type on any given day for any
origin-destination pair is controlled by a number of k-factors, which are used 
to create some correlation across various dimensions of demand.

Three k-factors are used to introduce correlation in demand across all markets in 
the system and between business/leisure demand within a market. The equation to 
generate the mean demand for a given market and passenger type 
is given as: 

$\mu'_{OD-Biz} = \mu_{OD-Biz} + (SRN \times k_{sys}) + (MRN \times k_{mkt}) + (PRN \times k_{paxtype})$ 

where SRN, MRN, and PRN are random numbers associated with the system, market, 
and passenger k-factors, respectively.

The intuition behind using three k-factors is that even across a "typical" departure 
day (like Wednesdays) we may have high demand days across the system and low demand 
days across the system.  Likewise, if business demand is above average, we expect 
that leisure demand may also be above average. Intuitively, when generating demands, 
for a given sample (or departure day in the simulation), we add the term 
(SRN x `sys_k_factor`) to every single market and passenger in the system for that 
departure day, we add a unique (MRN x `mkt_k_factor`) to each origin-destination 
market in the sample, and we add a unique (PRN x `pax_type_k_factor`) for each 
passenger type within the market. The addition of the (SRN x `sys_k_factor`) to 
"everything" in the sample creates a system-level correlation (i.e., demand on 
a given departure date or sample could be "high" across the system or "low" 
compared to average).  

The addition of the (MRN x `mkt_k_factor`) to a market creates a market-level 
correlation (i.e., if business demand is running higher than average in the 
market, we expect leisure demand will run higher than average in general as 
well).  

The use of the (PRN x `pax_type_k_factor`) ensures that there is some random 
component that is independent between business and leisure passengers in a 
given market.

In addition to the k-factors that are used to introduce correlation, we have a z-factor.  
We assume that actual demand, given mean demand, will vary across samples (or 
departure dates) according to a constant z-factor given as $\mu$ divided by $\sigma^2$. 

Given different levels of aggregation, we expect that `sys_k_factor` < `mkt_k_factor` < `pax_type_k_factor`.

Once we generate the means and std dev for correlated demands by OD and pax type 
using the methodology described above, we use these to generate the “actual” demands 
for a sample using the equation

$\mu'_{OD-Biz} + NRV x \sigma'_{OD-Biz}$, 

where NRV is a normal random variable.


## Demand Allocation to Time Periods

The demand generation above is used to find the total demand for each passenger
type in each market on each travel day.  This total value is subsequently distributed 
over the booking time periods.

While the methodology for this is not (yet) explained here, note that the `tf_k_factor` 
is used to generate variability in how demand is allocated to the different time 
frames (also using the booking curves as a key input).

