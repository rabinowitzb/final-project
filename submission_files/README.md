To begin using HAMBRE, one should enter flask run, and follow the link. They are led to our landing page, which in addition to featuring an About Us description, gives the user the option to login, or register as a chef or customer.
For HAMBRE to work properly, we recommend first registering as a chef, and then following the workflows from there.

If the user is a first time customer, they are led to a customer registration page, where they input basic information, including their diet preference. Importantly, they must agree to submitting their location, as their geographical coordinates are critical to our pairing them with a chef.
We assume that the user will be able to pay their credit card bill :)
We also assume that the user will remain in the same timezone which they originally registered.
If the user is a returning customer, they simply login.
After submitting the form, they are led to a meal suggestions page, which depending on their diet and time of day (i.e. breakfast is offered between 8:01 AM and 11:59 AM), will feature 5 meals (and pertinent dietary information) which they can add to their cart by selecting the options and submitting the form.
They can then see their cart before they checkout. Once they checkout, they are notified on ordered.html which chef will make their meals, and where they can pickup that food (i.e. the chef's location).
Also, the customer can see their history of orders in their customer history page.
Also, because we clear the session every time a user logs out, a customer loses their cart when they log out.

An intriguing feature which we built is that a customer is offered meals prepared by the chef closest to them, so time for pickup is minimized.
(We assume that there are enough chefs in the system such that wherever and whenever you order there will be a chef able to prepare the meal.)

If the user is a first time chef, instead of registering as a customer, they should register as a chef. After completing the registration form, they are led their cheforders page, where they can see their entire history of orders.
If the user is a returning chef, they simply login.
Unlike the customer experience, the chef only sees one page with all of their active, or "incomplete", and "complete" orders together.
Once a customer checks out a meal, the chef to whom the meal is assigned receives a new entry in their cheforders portal with a new meal request.
The meal is inserted into their cheforders table with an "incomplete" status. Only after the meal is ready for pickup, the chef can change the status of the meal to "complete" in both cheforders and customerhistory.
(We further assume that all chefs can make all meals, and that they can theoretically have an infinite number of "incomplete" orders to make at a time.)

Lastly, we assume that at least one chef and one customer will be registered with HAMBRE at any moment.