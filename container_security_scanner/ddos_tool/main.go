package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"sync"
)

// worker sends a single HTTP request and reports the result.
func worker(wg *sync.WaitGroup, url string, results chan<- int) {
	defer wg.Done()

	resp, err := http.Get(url)
	if err != nil {
		// Print the specific error to stderr for diagnosis
		fmt.Fprintf(os.Stderr, "Request Error: %v\n", err)
		results <- 0 // 0 for failure
		return
	}
	defer resp.Body.Close()
	results <- resp.StatusCode
}

func main() {
	url := flag.String("url", "", "URL to target")
	requests := flag.Int("n", 10, "Number of requests")
	concurrency := flag.Int("c", 5, "Number of concurrent workers")
	flag.Parse()

	if *url == "" {
		fmt.Println("URL is required")
		flag.Usage()
		os.Exit(1)
	}

	var wg sync.WaitGroup
	results := make(chan int, *requests)
	// Use a buffered channel to control concurrency.
	// This channel acts as a semaphore.
	sem := make(chan struct{}, *concurrency)

	fmt.Printf("Starting DDoS simulation on %s with %d requests and %d concurrency...\n", *url, *requests, *concurrency)

	for i := 0; i < *requests; i++ {
		wg.Add(1)
		sem <- struct{}{} // Acquire a spot
		go func() {
			defer func() { <-sem }() // Release the spot
			worker(&wg, *url, results)
		}()
	}

	wg.Wait()
	close(results)

	successCount := 0
	failureCount := 0
	statusCodeCounts := make(map[int]int)

	for res := range results {
		if res >= 200 && res < 300 {
			successCount++
		} else {
			failureCount++
		}
		statusCodeCounts[res]++
	}

	fmt.Println("\n--- Results ---")
	fmt.Printf("Total Requests: %d\n", *requests)
	fmt.Printf("Successful Requests: %d\n", successCount)
	fmt.Printf("Failed Requests: %d\n", failureCount)
	fmt.Println("Status Code Distribution:")
	for code, count := range statusCodeCounts {
		fmt.Printf("  %d: %d\n", code, count)
	}
}
