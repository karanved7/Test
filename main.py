from recipes import get_daily_meals


def print_recipe(label, recipe):
    print(f"\n{'='*45}")
    print(f"  {label}: {recipe['name']}")
    print(f"{'='*45}")
    print(f"  Cost: {recipe['cost']}  |  Calories: {recipe['calories']} kcal  |  Time: {recipe['time']}")
    print(f"\n  Ingredients:")
    for item in recipe["ingredients"]:
        print(f"    - {item}")
    print(f"\n  Steps:")
    for i, step in enumerate(recipe["steps"], 1):
        print(f"    {i}. {step}")


def main():
    print("\n========================================")
    print("   Healthy Budget Meal Planner")
    print("   2 meals a day | Fresh & Affordable")
    print("========================================")

    meal1, meal2 = get_daily_meals()

    print_recipe("MEAL 1", meal1)
    print_recipe("MEAL 2", meal2)

    cost1 = float(meal1["cost"].replace("$", ""))
    cost2 = float(meal2["cost"].replace("$", ""))
    total_cal = meal1["calories"] + meal2["calories"]
    total_cost = cost1 + cost2

    print(f"\n{'='*45}")
    print(f"  Daily Total: ${total_cost:.2f}  |  {total_cal} kcal")
    print(f"{'='*45}\n")

    while True:
        again = input("Get new meals? (y/n): ").strip().lower()
        if again == "y":
            meal1, meal2 = get_daily_meals()
            print_recipe("MEAL 1", meal1)
            print_recipe("MEAL 2", meal2)
            cost1 = float(meal1["cost"].replace("$", ""))
            cost2 = float(meal2["cost"].replace("$", ""))
            total_cal = meal1["calories"] + meal2["calories"]
            total_cost = cost1 + cost2
            print(f"\n{'='*45}")
            print(f"  Daily Total: ${total_cost:.2f}  |  {total_cal} kcal")
            print(f"{'='*45}\n")
        elif again == "n":
            print("Enjoy your meals! Stay healthy.\n")
            break
        else:
            print("Please enter y or n.")


if __name__ == "__main__":
    main()
