#!/usr/bin/env python
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def test_health_check():
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy: {data['status']}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not connect to API: {str(e)}")
        print_info("Make sure server is running: python manage.py runserver")
        return False

def test_short_route():
    print_header("TEST 2: Short Route (Boston to Philadelphia)")
    
    payload = {
        "start_location": "Boston, MA",
        "end_location": "Philadelphia, PA"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimize-route/", json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            distance = data.get('total_distance_miles', 0)
            cost = data.get('total_estimated_fuel_cost', 0)
            stops = len(data.get('fuel_stops', []))
            
            print_success(f"Distance: {distance} miles")
            print_success(f"Estimated cost: ${cost:.2f}")
            print_success(f"Fuel stops needed: {stops}")
            return stops == 0
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_medium_route():
    print_header("TEST 3: Medium Route (Chicago to Miami)")
    
    payload = {
        "start_location": "Chicago, IL",
        "end_location": "Miami, FL"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimize-route/", json=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            distance = data.get('total_distance_miles', 0)
            cost = data.get('total_estimated_fuel_cost', 0)
            stops = len(data.get('fuel_stops', []))
            
            print_success(f"Distance: {distance} miles")
            print_success(f"Estimated cost: ${cost:.2f}")
            print_success(f"Fuel stops needed: {stops}")
            return stops > 0
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_long_route():
    print_header("TEST 4: Long Route (New York to Los Angeles)")
    
    payload = {
        "start_location": "New York, NY",
        "end_location": "Los Angeles, CA"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimize-route/", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            distance = data.get('total_distance_miles', 0)
            cost = data.get('total_estimated_fuel_cost', 0)
            stops = len(data.get('fuel_stops', []))
            
            print_success(f"Distance: {distance} miles")
            print_success(f"Estimated cost: ${cost:.2f}")
            print_success(f"Fuel stops: {stops}")
            
            if stops > 0:
                print_info(f"First stop: {data['fuel_stops'][0]['name']}")
            return stops > 0
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_fuel_stops():
    print_header("TEST 5: Get Fuel Stops by State")
    
    try:
        response = requests.get(f"{BASE_URL}/fuel-stops/?state=TX&limit=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_stops', 0)
            displayed = data.get('displayed_stops', 0)
            
            print_success(f"Total stops in TX: {total}")
            print_success(f"Displayed: {displayed}")
            
            for stop in data.get('stops', [])[:3]:
                print_info(f"  {stop['name']} - ${stop['price_per_gallon']:.2f}/gal")
            
            return True
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_invalid_location():
    print_header("TEST 6: Invalid Location Handling")
    
    payload = {
        "start_location": "InvalidCityXYZ123",
        "end_location": "AnotherFakeCity456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimize-route/", json=payload, timeout=15)
        
        if response.status_code != 200:
            print_success("Invalid locations correctly rejected")
            return True
        else:
            print_error("Should have rejected invalid locations")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_missing_params():
    print_header("TEST 7: Missing Parameters")
    
    payload = {"start_location": "New York, NY"}
    
    try:
        response = requests.post(f"{BASE_URL}/optimize-route/", json=payload, timeout=10)
        
        if response.status_code == 400:
            print_success("Missing parameters correctly rejected")
            return True
        else:
            print_error("Should have rejected missing parameters")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def run_all_tests():
    print(f"\n{Colors.BLUE}Fuel Route Optimizer API Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Starting tests...{Colors.END}\n")
    
    results = []
    results.append(("Health Check", test_health_check()))
    
    if not results[0][1]:
        print_error("\nCannot proceed with tests. API is not responding.")
        return
    
    time.sleep(1)
    results.append(("Short Route", test_short_route()))
    time.sleep(1)
    results.append(("Medium Route", test_medium_route()))
    time.sleep(1)
    results.append(("Long Route", test_long_route()))
    time.sleep(1)
    results.append(("Fuel Stops", test_fuel_stops()))
    time.sleep(1)
    results.append(("Invalid Location", test_invalid_location()))
    time.sleep(1)
    results.append(("Missing Params", test_missing_params()))
    
    print_header("TEST RESULTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name}: {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Results: {Colors.GREEN}{passed}/{total} passed{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    run_all_tests()
