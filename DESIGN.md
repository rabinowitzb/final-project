In making HAMBRE, we used several languages: Python, HTML, JavaScript, SQL, and CSS.
We used Python to write the logic of our application, HTML for the structure of our webpages, JavaScript to make them more dynamic, SQL to interact with our databases, and CSS to improve the aesthetics of HAMBRE.
We decided that it made most sense to divide the workflows and databases into two main paths -- chefs and customers -- because the ways in which they interact with HAMBRE are so different.

We decided to make 6 databases to keep things organized -- chefs, chefsorders (which has a history of the chef's orders, including their statuses), customers, customerscart, customershistory, and menu (into which we hardcoded meal options).
In register(s), HAMBRE detects that a username isn't taken in either chefs or customers by querying both databases; a username has to be unique to both chefs and customers for it to be valid.
In finding which meals to display on the mealsuggestions page, we find the current time using the python function datetime (in login or register(s)), set a mealtype (i.e. breakfast, lunch, or dinner) to each range of times, and display the meals which share that mealtype (and mealplan of the user) in menu.
In finding which chef to pair with which customer, we take both customer and chef coordinates (in login or register(s)) and then find the chef closest to the customer using a function we wrote in Python.

It is intentional that a user can only get one of each meal per cart order -- it is a diet website after all!
The customer learns the name of the chef preparing their meal when they view their cart because it would have been cluttered to show the name of the chef on the mealsuggestions page.
Lastly, in a sense, HAMBRE also functions like a social network, because it connects chefs and customers; the customer interacts with the chef when they pick up their meal.
