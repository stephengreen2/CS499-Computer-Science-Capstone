//============================================================================
// Name        : EnhancedVectorSorting.cpp
// Author      : Stephen Green (Enhanced)
// Version     : 2.0
// Copyright   : Copyright © 2023 SNHU COCE
// Description : Enhanced Vector Sorting Algorithms with Benchmarking
//============================================================================

#include <algorithm>
#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <iomanip>
#include <limits>
#include <stdexcept>

#include "CSVparser.hpp"

using namespace std;
using namespace std::chrono;

//============================================================================
// Global definitions and structures
//============================================================================

/**
 * Structure to hold bid information
 */
struct Bid {
    string bidId;    // unique identifier
    string title;    // bid title for sorting
    string fund;     // fund information
    double amount;   // bid amount

    Bid() : amount(0.0) {}
};

/**
 * Structure to hold benchmark results for sorting algorithms
 */
struct BenchmarkResult {
    string algorithmName;
    size_t dataSize;
    double executionTimeMs;

    BenchmarkResult(const string& name, size_t size, double time)
        : algorithmName(name), dataSize(size), executionTimeMs(time) {
    }
};

//============================================================================
// Sorting Algorithms Class
//============================================================================

/**
 * Class containing various sorting algorithms for Bid objects
 * Provides modular, reusable sorting functionality with performance tracking
 */
class BidSorter {
private:
    /**
     * Partition function for quicksort algorithm
     * Divides the vector into two parts around a pivot element
     *
     * @param bids Reference to vector of Bid objects to partition
     * @param begin Starting index for partition
     * @param end Ending index for partition
     * @return Index of the partition point
     */
    static size_t partition(vector<Bid>& bids, size_t begin, size_t end) {
        if (begin >= end) return begin;

        size_t lowIndex = begin;
        size_t highIndex = end;

        // Use middle element as pivot to improve average case performance
        size_t middlePoint = lowIndex + (highIndex - lowIndex) / 2;
        string pivot = bids[middlePoint].title;

        while (true) {
            // Find element greater than or equal to pivot from left
            while (lowIndex <= end && bids[lowIndex].title < pivot) {
                lowIndex++;
            }

            // Find element less than or equal to pivot from right
            while (highIndex >= begin && pivot < bids[highIndex].title) {
                highIndex--;
            }

            // If pointers have crossed, partitioning is complete
            if (highIndex <= lowIndex) {
                return highIndex;
            }

            // Swap elements and continue
            swap(bids[lowIndex], bids[highIndex]);
            lowIndex++;
            highIndex--;
        }
    }

    /**
     * Merge function for merge sort algorithm
     * Combines two sorted subarrays into a single sorted array
     *
     * @param bids Reference to vector of Bid objects
     * @param left Starting index of left subarray
     * @param mid Ending index of left subarray
     * @param right Ending index of right subarray
     */
    static void merge(vector<Bid>& bids, size_t left, size_t mid, size_t right) {
        // Create temporary arrays for left and right subarrays
        vector<Bid> leftArray(bids.begin() + left, bids.begin() + mid + 1);
        vector<Bid> rightArray(bids.begin() + mid + 1, bids.begin() + right + 1);

        size_t i = 0, j = 0, k = left;

        // Merge the temporary arrays back into bids[left..right]
        while (i < leftArray.size() && j < rightArray.size()) {
            if (leftArray[i].title <= rightArray[j].title) {
                bids[k] = leftArray[i];
                i++;
            }
            else {
                bids[k] = rightArray[j];
                j++;
            }
            k++;
        }

        // Copy remaining elements of leftArray, if any
        while (i < leftArray.size()) {
            bids[k] = leftArray[i];
            i++;
            k++;
        }

        // Copy remaining elements of rightArray, if any
        while (j < rightArray.size()) {
            bids[k] = rightArray[j];
            j++;
            k++;
        }
    }

public:
    /**
     * Selection Sort Algorithm
     * Time Complexity: O(n²) average and worst case
     * Space Complexity: O(1)
     *
     * @param bids Reference to vector of Bid objects to sort
     */
    static void selectionSort(vector<Bid>& bids) {
        if (bids.empty()) return;

        size_t size = bids.size();

        for (size_t i = 0; i < size - 1; ++i) {
            size_t minIndex = i;

            // Find the minimum element in remaining unsorted array
            for (size_t j = i + 1; j < size; ++j) {
                if (bids[j].title < bids[minIndex].title) {
                    minIndex = j;
                }
            }

            // Swap the found minimum element with the first element
            if (minIndex != i) {
                swap(bids[i], bids[minIndex]);
            }
        }
    }

    /**
     * Quick Sort Algorithm (Recursive Implementation)
     * Time Complexity: O(n log n) average case, O(n²) worst case
     * Space Complexity: O(log n) average case due to recursion
     *
     * @param bids Reference to vector of Bid objects to sort
     * @param begin Starting index for sorting
     * @param end Ending index for sorting
     */
    static void quickSort(vector<Bid>& bids, size_t begin, size_t end) {
        if (bids.empty() || end <= begin) return;

        // Partition the array and get the pivot index
        size_t pivotIndex = partition(bids, begin, end);

        // Recursively sort elements before and after partition
        if (pivotIndex > begin) {
            quickSort(bids, begin, pivotIndex);
        }
        if (pivotIndex < end) {
            quickSort(bids, pivotIndex + 1, end);
        }
    }

    /**
     * Merge Sort Algorithm (Recursive Implementation)
     * Time Complexity: O(n log n) guaranteed
     * Space Complexity: O(n) for temporary arrays
     *
     * @param bids Reference to vector of Bid objects to sort
     * @param left Starting index for sorting
     * @param right Ending index for sorting
     */
    static void mergeSort(vector<Bid>& bids, size_t left, size_t right) {
        if (bids.empty() || left >= right) return;

        // Find the middle point to divide the array into two halves
        size_t mid = left + (right - left) / 2;

        // Recursively sort first and second halves
        mergeSort(bids, left, mid);
        mergeSort(bids, mid + 1, right);

        // Merge the sorted halves
        merge(bids, left, mid, right);
    }

    /**
     * Heap Sort Algorithm
     * Time Complexity: O(n log n) guaranteed
     * Space Complexity: O(1)
     *
     * @param bids Reference to vector of Bid objects to sort
     */
    static void heapSort(vector<Bid>& bids) {
        if (bids.empty()) return;

        // Lambda function to heapify a subtree rooted at index i
        auto heapify = [&bids](size_t n, size_t i) {
            auto heapifyRecursive = [&bids](size_t n, size_t i, auto& self) -> void {
                size_t largest = i;    // Initialize largest as root
                size_t left = 2 * i + 1;   // left child
                size_t right = 2 * i + 2;  // right child

                // If left child is larger than root
                if (left < n && bids[left].title > bids[largest].title) {
                    largest = left;
                }

                // If right child is larger than largest so far
                if (right < n && bids[right].title > bids[largest].title) {
                    largest = right;
                }

                // If largest is not root
                if (largest != i) {
                    swap(bids[i], bids[largest]);
                    // Recursively heapify the affected sub-tree
                    self(n, largest, self);
                }
                };
            heapifyRecursive(n, i, heapifyRecursive);
            };

        size_t n = bids.size();

        // Build heap (rearrange array)
        for (int i = n / 2 - 1; i >= 0; i--) {
            heapify(n, i);
        }

        // Extract elements from heap one by one
        for (size_t i = n - 1; i > 0; i--) {
            // Move current root to end
            swap(bids[0], bids[i]);

            // Call max heapify on the reduced heap
            heapify(i, 0);
        }
    }
};

//============================================================================
// Benchmarking and Utility Functions
//============================================================================

/**
 * Benchmarks a sorting algorithm and returns execution time
 *
 * @param sortFunction Function pointer to the sorting algorithm
 * @param bids Vector of bids to sort (will be copied for testing)
 * @param algorithmName Name of the algorithm for reporting
 * @return BenchmarkResult containing timing information
 */
template<typename SortFunc>
BenchmarkResult benchmarkSort(SortFunc sortFunction, vector<Bid> bids, const string& algorithmName) {
    if (bids.empty()) {
        return BenchmarkResult(algorithmName, 0, 0.0);
    }

    auto start = high_resolution_clock::now();

    // Execute the sorting algorithm
    if constexpr (is_same_v<SortFunc, decltype(&BidSorter::quickSort)> ||
        is_same_v<SortFunc, decltype(&BidSorter::mergeSort)>) {
        // For algorithms that need begin/end parameters
        sortFunction(bids, 0, bids.size() - 1);
    }
    else {
        // For algorithms that take only the vector
        sortFunction(bids);
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);

    return BenchmarkResult(algorithmName, bids.size(), duration.count() / 1000.0);
}

/**
 * Displays benchmark results in a formatted table
 *
 * @param results Vector of benchmark results to display
 */
void displayBenchmarks(const vector<BenchmarkResult>& results) {
    if (results.empty()) {
        cout << "No benchmark results to display." << endl;
        return;
    }

    cout << "\n" << string(70, '=') << endl;
    cout << "SORTING ALGORITHM PERFORMANCE COMPARISON" << endl;
    cout << string(70, '=') << endl;

    cout << left << setw(20) << "Algorithm"
        << setw(15) << "Data Size"
        << setw(20) << "Time (ms)"
        << setw(15) << "Complexity" << endl;
    cout << string(70, '-') << endl;

    for (const auto& result : results) {
        string complexity;
        if (result.algorithmName == "Selection Sort") {
            complexity = "O(n²)";
        }
        else if (result.algorithmName == "Quick Sort") {
            complexity = "O(n log n)";
        }
        else if (result.algorithmName == "Merge Sort") {
            complexity = "O(n log n)";
        }
        else if (result.algorithmName == "Heap Sort") {
            complexity = "O(n log n)";
        }

        cout << left << setw(20) << result.algorithmName
            << setw(15) << result.dataSize
            << setw(20) << fixed << setprecision(3) << result.executionTimeMs
            << setw(15) << complexity << endl;
    }
    cout << string(70, '=') << endl;
}

/**
 * Validates integer input from user
 *
 * @param prompt Message to display to user
 * @param min Minimum acceptable value
 * @param max Maximum acceptable value
 * @return Valid integer within specified range
 */
int getValidatedInput(const string& prompt, int min = 1, int max = 10) {
    int choice;
    while (true) {
        cout << prompt;
        if (cin >> choice && choice >= min && choice <= max) {
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            return choice;
        }
        else {
            cout << "Invalid input. Please enter a number between "
                << min << " and " << max << "." << endl;
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
        }
    }
}

/**
 * Converts string to double after removing specified character
 *
 * @param str Input string to convert
 * @param ch Character to remove from string
 * @return Converted double value
 */
double strToDouble(string str, char ch) {
    str.erase(remove(str.begin(), str.end(), ch), str.end());
    try {
        return stod(str);
    }
    catch (const invalid_argument& e) {
        return 0.0;
    }
}

/**
 * Displays bid information to console
 *
 * @param bid Bid object to display
 */
void displayBid(const Bid& bid) {
    cout << bid.bidId << ": " << bid.title << " | $"
        << fixed << setprecision(2) << bid.amount << " | " << bid.fund << endl;
}

/**
 * Prompts user for bid information
 *
 * @return Bid object with user-entered information
 */
Bid getBid() {
    Bid bid;

    cout << "Enter Id: ";
    cin.ignore();
    getline(cin, bid.bidId);

    cout << "Enter title: ";
    getline(cin, bid.title);

    cout << "Enter fund: ";
    getline(cin, bid.fund);

    cout << "Enter amount: ";
    string strAmount;
    getline(cin, strAmount);
    bid.amount = strToDouble(strAmount, '$');

    return bid;
}

/**
 * Loads bids from CSV file
 *
 * @param csvPath Path to the CSV file
 * @return Vector of Bid objects loaded from file
 */
vector<Bid> loadBids(const string& csvPath) {
    cout << "Loading CSV file: " << csvPath << endl;
    vector<Bid> bids;

    try {
        csv::Parser file(csvPath);

        cout << "Processing " << file.rowCount() << " rows..." << endl;

        for (int i = 0; i < file.rowCount(); i++) {
            Bid bid;
            bid.bidId = file[i][1];
            bid.title = file[i][0];
            bid.fund = file[i][8];
            bid.amount = strToDouble(file[i][4], '$');

            bids.push_back(bid);
        }

        cout << "Successfully loaded " << bids.size() << " bids." << endl;

    }
    catch (const csv::Error& e) {
        cerr << "CSV Error: " << e.what() << endl;
    }
    catch (const exception& e) {
        cerr << "Error loading file: " << e.what() << endl;
    }

    return bids;
}

/**
 * Runs comprehensive benchmark comparing all sorting algorithms
 *
 * @param bids Vector of bids to benchmark
 */
void runBenchmarkComparison(const vector<Bid>& bids) {
    if (bids.empty()) {
        cout << "No data available for benchmarking. Please load bids first." << endl;
        return;
    }

    cout << "\nRunning comprehensive benchmark on " << bids.size() << " items..." << endl;
    vector<BenchmarkResult> results;

    // Benchmark Selection Sort
    results.push_back(benchmarkSort(&BidSorter::selectionSort, bids, "Selection Sort"));

    // Benchmark Quick Sort
    results.push_back(benchmarkSort(&BidSorter::quickSort, bids, "Quick Sort"));

    // Benchmark Merge Sort
    results.push_back(benchmarkSort(&BidSorter::mergeSort, bids, "Merge Sort"));

    // Benchmark Heap Sort
    results.push_back(benchmarkSort(&BidSorter::heapSort, bids, "Heap Sort"));

    displayBenchmarks(results);
}

//============================================================================
// Main Program
//============================================================================

/**
 * Displays the main menu options
 */
void displayMenu() {
    cout << "\n" << string(50, '=') << endl;
    cout << "ENHANCED BID SORTING SYSTEM" << endl;
    cout << string(50, '=') << endl;
    cout << "1. Load Bids from CSV" << endl;
    cout << "2. Display All Bids" << endl;
    cout << "3. Add Manual Bid Entry" << endl;
    cout << "4. Selection Sort (O(n²))" << endl;
    cout << "5. Quick Sort (O(n log n))" << endl;
    cout << "6. Merge Sort (O(n log n))" << endl;
    cout << "7. Heap Sort (O(n log n))" << endl;
    cout << "8. Run Benchmark Comparison" << endl;
    cout << "9. Clear All Bids" << endl;
    cout << "10. Exit" << endl;
    cout << string(50, '=') << endl;
}

/**
 * Main function - Program entry point
 */
int main(int argc, char* argv[]) {
    // Process command line arguments
    string csvPath = (argc == 2) ? argv[1] : "eBid_Monthly_Sales.csv";

    vector<Bid> bids;

    cout << "Enhanced Vector Sorting System v2.0" << endl;
    cout << "Default CSV file: " << csvPath << endl;

    int choice = 0;
    while (choice != 10) {
        displayMenu();
        choice = getValidatedInput("Enter your choice (1-10): ", 1, 10);

        switch (choice) {
        case 1: {
            auto start = high_resolution_clock::now();
            bids = loadBids(csvPath);
            auto end = high_resolution_clock::now();
            auto duration = duration_cast<milliseconds>(end - start);
            cout << "Load time: " << duration.count() << " ms" << endl;
            break;
        }

        case 2:
            if (bids.empty()) {
                cout << "No bids to display. Please load data first." << endl;
            }
            else {
                cout << "\nDisplaying " << bids.size() << " bids:" << endl;
                cout << string(60, '-') << endl;
                for (const auto& bid : bids) {
                    displayBid(bid);
                }
            }
            break;

        case 3: {
            Bid newBid = getBid();
            bids.push_back(newBid);
            cout << "Bid added successfully. Total bids: " << bids.size() << endl;
            break;
        }

        case 4: {
            if (bids.empty()) {
                cout << "No data to sort. Please load bids first." << endl;
                break;
            }
            auto result = benchmarkSort(&BidSorter::selectionSort, bids, "Selection Sort");
            bids = loadBids(csvPath);  // Reload for sorting
            BidSorter::selectionSort(bids);
            cout << "Selection Sort completed in " << result.executionTimeMs << " ms" << endl;
            break;
        }

        case 5: {
            if (bids.empty()) {
                cout << "No data to sort. Please load bids first." << endl;
                break;
            }
            auto result = benchmarkSort(&BidSorter::quickSort, bids, "Quick Sort");
            if (bids.size() > 0) {
                BidSorter::quickSort(bids, 0, bids.size() - 1);
            }
            cout << "Quick Sort completed in " << result.executionTimeMs << " ms" << endl;
            break;
        }

        case 6: {
            if (bids.empty()) {
                cout << "No data to sort. Please load bids first." << endl;
                break;
            }
            auto result = benchmarkSort(&BidSorter::mergeSort, bids, "Merge Sort");
            if (bids.size() > 0) {
                BidSorter::mergeSort(bids, 0, bids.size() - 1);
            }
            cout << "Merge Sort completed in " << result.executionTimeMs << " ms" << endl;
            break;
        }

        case 7: {
            if (bids.empty()) {
                cout << "No data to sort. Please load bids first." << endl;
                break;
            }
            auto result = benchmarkSort(&BidSorter::heapSort, bids, "Heap Sort");
            BidSorter::heapSort(bids);
            cout << "Heap Sort completed in " << result.executionTimeMs << " ms" << endl;
            break;
        }

        case 8:
            runBenchmarkComparison(bids);
            break;

        case 9:
            bids.clear();
            cout << "All bids cleared from memory." << endl;
            break;

        case 10:
            cout << "Thank you for using Enhanced Vector Sorting System!" << endl;
            break;
        }

        if (choice != 10) {
            cout << "\nPress Enter to continue...";
            cin.ignore();
            cin.get();
        }
    }

    return 0;
}