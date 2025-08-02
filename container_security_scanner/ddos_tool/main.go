package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"sync"
)

// worker は単一の HTTP リクエストを送信し、結果を報告
func worker(wg *sync.WaitGroup, url string, results chan<- int) {
	defer wg.Done()

	resp, err := http.Get(url)
	if err != nil {
		// 診断のために特定のエラーを stderr に出力
		fmt.Fprintf(os.Stderr, "Request Error: %v\n", err)
		results <- 0 // 失敗の場合は 0
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
	// バッファ付きチャネルを使用して同時実行性を制御
	// このチャネルはセマフォとして機能
	sem := make(chan struct{}, *concurrency)

	fmt.Printf("Starting DDoS simulation on %s with %d requests and %d concurrency...\n", *url, *requests, *concurrency)

	for i := 0; i < *requests; i++ {
		wg.Add(1)
		sem <- struct{}{} // スポットを取得
		go func() {
			defer func() { <-sem }() // スポットを解放
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
