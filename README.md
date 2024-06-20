# FACTORY SIMULATION
#### Video Demo:  <URL HERE>
#### Description:
- You're looking at my final project for CS50P. I wanted the project to be a little bit more complex than the base requirements. The point was to experience the problems and difficulties that can occur when complexity goes up. I work in manufacturing so I picked a topic that I already know some stuff about. In the industry ERP software such as SAP is used for that effect. 

- The program mimics the behaviour of an ERP system in very simplistic terms. So in that way it simulates a running factory. The user interface of the app runs on the cli through the textual library. The program randomly generates products that you can produce and sell. You can create workorders from those products that are automatically assigned to the appropriate workcenters. It generates workcenters in which you can manufacture the parts and then assemble them into final products. You can buy raw materials for the part manufacturing, transfer the raw materials from the warehouse to the workcenters and so on and so forth. There is a randomly generated market that you changes everyday. You can buy raw materials and sell end products depending on the market conditions. The last 30 days of the prices are given to the user so they can see trends and better condition when they appear.

There are 5 main modules, 
* Sales 
* Production 
* Planning 
* Logistics
* Procurement

#### Sales
* You can sell the products you have in the storage.
* You can view general information about the prices and manufacturing costs of the end products.
* You can view the orders you have for the products.
* You can view the prices for the last 30 days for each product.
* You can view a summary for the market condition of the day.
* The end products are divided into several categories like,
  - Heating and Cooling
  - Entertainment and Information
  - Kitchen Appliances
  - etc.
* Each product category has different modifiers that effect its price every day.

#### Production
* You can view workcenters and related information such as the number of operators working.
* There are 7 categories of workcenters,
  - Machining
  - Bending
  - Casting
  - Forging
  - Paintjob
  - Welding
  - Assembly
* You can view the operations assigned to each workcenter.
* Each operation is related to the certain production method.

#### Planning
* You can view general information about products and its manufacturing.
* You can view the bill of materials.
* You can view the workorders and its operations.
* You can create or delete workorders.
* You can view the load on each workcenter.

#### Logistics
* You can view the warehouse and its shelves.
* You can view stock numbers and the shelf addresses of each part.
* You can purchase new shelves for the warehouse.
* You can view the raw material stocks.
* You can transfer raw materails to the workcenters.

#### Procurement
* You can purchase raw materials.
* You can view the price for the last 30 days for each raw material.
* You can view general information about each raw material.
* You can view the market conditions for each day.
* You can view the how many raw materails will be consumed for each workorder.

#### End Day
* After making the decisions for the day you can press the "End Day" button and push the calender one day forward.
* Market conditions will be recalculated.
* Products in the selling list will be sold.
* Each active workcenter will be run.
* Workcenters concurrently run as many operation as thare are operators in that workcenter.



