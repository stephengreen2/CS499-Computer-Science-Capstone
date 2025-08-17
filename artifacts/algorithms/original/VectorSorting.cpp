//============================================================================
// Name        : VectorSorting.cpp
// Author      : Your name
// Version     : 1.0
// Copyright   : Copyright © 2023 SNHU COCE
// Description : Vector Sorting Algorithms
//============================================================================

#include <algorithm>
#include <iostream>
#include <time.h>

#include "CSVparser.hpp"

using namespace std;

//============================================================================
// Global definitions visible to all methods and classes
//============================================================================

// forward declarations
double strToDouble(string str, char ch);

// define a structure to hold bid information
struct Bid {
    string bidId; // unique identifier
    string title;
    string fund;
    double amount;
    Bid() {
        amount = 0.0;
    }
};

//============================================================================
// Static methods used for testing
//============================================================================

/**
 * Display the bid information to the console (std::out)
 *
 * @param bid struct containing the bid info
 */
void displayBid(Bid bid) {
    cout << bid.bidId << ": " << bid.title << " | " << bid.amount << " | "
            << bid.fund << endl;
    return;
}

/**
 * Prompt user for bid information using console (std::in)
 *
 * @return Bid struct containing the bid info
 */
Bid getBid() {
    Bid bid;

    cout << "Enter Id: ";
    cin.ignore();
    getline(cin, bid.bidId);

    cout << "Enter title: ";
    getline(cin, bid.title);

    cout << "Enter fund: ";
    cin >> bid.fund;

    cout << "Enter amount: ";
    cin.ignore();
    string strAmount;
    getline(cin, strAmount);
    bid.amount = strToDouble(strAmount, '$');

    return bid;
}

/**
 * Load a CSV file containing bids into a container
 *
 * @param csvPath the path to the CSV file to load
 * @return a container holding all the bids read
 */
vector<Bid> loadBids(string csvPath) {
    cout << "Loading CSV file " << csvPath << endl;

    // Define a vector data structure to hold a collection of bids.
    vector<Bid> bids;

    // initialize the CSV Parser using the given path
    csv::Parser file = csv::Parser(csvPath);

    try {
        // loop to read rows of a CSV file
        for (int i = 0; i < file.rowCount(); i++) {

            // Create a data structure and add to the collection of bids
            Bid bid;
            bid.bidId = file[i][1];
            bid.title = file[i][0];
            bid.fund = file[i][8];
            bid.amount = strToDouble(file[i][4], '$');

            //cout << "Item: " << bid.title << ", Fund: " << bid.fund << ", Amount: " << bid.amount << endl;

            // push this bid to the end
            bids.push_back(bid);
        }
    } catch (csv::Error &e) {
        std::cerr << e.what() << std::endl;
    }
    return bids;
}

/**
 * Partition the vector of bids into two parts, low and high
 *
 * @param bids Address of the vector<Bid> instance to be partitioned
 * @param begin Beginning index to partition
 * @param end Ending index to partition
 */
size_t partition(vector<Bid>& bids, size_t begin, size_t end) {
    size_t lowIndex = begin;
    size_t highIndex = end;

    // Calculate the middle element as middlePoint (int)
    size_t middlePoint = lowIndex + (highIndex - lowIndex) / 2;

    // Set Pivot as middlePoint element title to compare (string)  
    string pivot = bids[middlePoint].title;

    while (true) {
        // keep incrementing low index while bids[low].title < Pivot
        while (bids[lowIndex].title < pivot) {
            lowIndex++;
        }

        // keep decrementing high index while Pivot < bids[high].title
        while (pivot < bids[highIndex].title) {
            highIndex--;
        }

        // check if all elements have been partitioned
        if (highIndex <= lowIndex) {
            return highIndex;
        }

        // swap low and high elements
        swap(bids[lowIndex], bids[highIndex]);

        // reposition low/high indexes closer
        lowIndex++;
        highIndex--;
    }

    return highIndex;
}

/**
 * Perform a quick sort on bid title
 * Average performance: O(n log(n))
 * Worst case performance O(n^2))
 *
 * @param bids address of the vector<Bid> instance to be sorted
 * @param begin the beginning index to sort on
 * @param end the ending index to sort on
 */
void quickSort(vector<Bid>& bids, size_t begin, size_t end) {
    // check if elements exist to be sorted
    if (end <= begin) {
        return;
    }

    // partition the elements to be sorted
    size_t mid = 0;
    mid = partition(bids, begin, end);

    // recursively sort low partition
    quickSort(bids, begin, mid);

    // recursively sort high partition
    quickSort(bids, mid + 1, end);
}

/**
 * Perform a selection sort on bid title
 * Average performance: O(n^2))
 * Worst case performance O(n^2))
 *
 * @param bid address of the vector<Bid>
 *            instance to be sorted
 */
void selectionSort(vector<Bid>& bids) {
    size_t min = 0;
    size_t size = bids.size();

    for (size_t pos = 0; pos < size - 1; ++pos) {
        min = pos;

        // find the next minimum title remaining after the current element
        for (size_t j = pos + 1; j < size; ++j) {
            if (bids[j].title < bids[min].title) {
                min = j;
            }
        }

        // swap the current element with the minimum element
        swap(bids[pos], bids[min]);
    }
}

/**
 * Simple C function to convert a string to a double
 * after stripping out unwanted char
 *
 * credit: http://stackoverflow.com/a/24875936
 *
 * @param ch The character to strip out
 */
double strToDouble(string str, char ch) {
    str.erase(remove(str.begin(), str.end(), ch), str.end());
    return atof(str.c_str());
}

static void displayTicks(clock_t ticks) {
    // Calculate elapsed time and display result
    ticks = clock() - ticks; // current clock ticks minus starting clock ticks
    cout << "time: " << ticks << " clock ticks" << endl;
    cout << "time: " << ticks * 1.0 / CLOCKS_PER_SEC << " seconds" << endl;
}

/**
 * The one and only main() method
 */
int main(int argc, char* argv[]) {

    // process command line arguments
    string csvPath;
    switch (argc) {
    case 2:
        csvPath = argv[1];
        break;
    default:
        csvPath = "eBid_Monthly_Sales.csv";
    }

    // Define a vector to hold all the bids
    vector<Bid> bids;

    // Define a timer variable
    clock_t ticks;

    int choice = 0;
    while (choice != 9) {
        cout << "Menu:" << endl;
        cout << "  1. Load Bids" << endl;
        cout << "  2. Display All Bids" << endl;
        cout << "  3. Selection Sort All Bids" << endl;
        cout << "  4. Quick Sort All Bids" << endl;
        cout << "  9. Exit" << endl;
        cout << "Enter choice: ";
        cin >> choice;

        switch (choice) {

        case 1:
            // Initialize a timer variable before loading bids
            ticks = clock();

            // Complete the method call to load the bids
            bids = loadBids(csvPath);

            cout << bids.size() << " bids read" << endl;

            // Calculate elapsed time and display result
            displayTicks(ticks);

            break;

        case 2:
            // Loop and display the bids read
            for (int i = 0; i < bids.size(); ++i) {
                displayBid(bids[i]);
            }
            cout << endl;

            break;

        // use selectionSort to order the bids by title
        case 3:
            ticks = clock();
            selectionSort(bids);

            // display the performance of the sort
            cout << bids.size() << " bids sorted" << endl;
            displayTicks(ticks);

            break;

        // use quickSort to order the bids by title
        case 4:
            size_t size = bids.size();

            ticks = clock();            
            quickSort(bids, 0, size - 1);            

            // display the performance of the sort
            cout << size << " bids sorted" << endl;
            displayTicks(ticks);

            break;
        }
    }

    cout << "Good bye." << endl;

    return 0;
}
