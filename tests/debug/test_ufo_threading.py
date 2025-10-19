"""
Test thread safety and concurrency issues in UFO Classifier
"""

import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.services.ufo_classifier_service import (
    UFOClassifierService,
    create_ufo_classifier_service,
    get_ufo_classifier,
)


def test_singleton_thread_safety():
    """Test singleton creation under concurrent access"""
    print("\n=== Testing Singleton Thread Safety ===")

    instances = queue.Queue()
    errors = queue.Queue()

    def get_instance_worker():
        try:
            instance = get_ufo_classifier()
            instances.put(id(instance))
        except Exception as e:
            errors.put(str(e))

    # Create many threads that all try to get the singleton
    threads = []
    for _ in range(50):
        t = threading.Thread(target=get_instance_worker)
        threads.append(t)

    # Start all threads simultaneously
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Check results
    if not errors.empty():
        print(f"Errors occurred: {list(errors.queue)}")

    instance_ids = list(instances.queue)
    unique_ids = set(instance_ids)

    print(f"Total instances created: {len(unique_ids)}")
    print(f"All instances same: {len(unique_ids) == 1}")

    if len(unique_ids) > 1:
        print(f"WARNING: Multiple instances created! IDs: {unique_ids}")


def test_concurrent_classification():
    """Test concurrent classifications for thread safety"""
    print("\n=== Testing Concurrent Classification ===")

    classifier = UFOClassifierService()
    results = queue.Queue()
    errors = queue.Queue()

    def classify_worker(worker_id):
        for i in range(10):
            try:
                result = classifier.classify(
                    f"term_{worker_id}_{i}",
                    f"definition for worker {worker_id} item {i}",
                )
                results.put((worker_id, i, result.primary_category.value))
            except Exception as e:
                errors.put((worker_id, i, str(e)))

    # Create threads
    threads = []
    num_workers = 20

    for worker_id in range(num_workers):
        t = threading.Thread(target=classify_worker, args=(worker_id,))
        threads.append(t)

    # Start all threads
    start_time = time.time()
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    # Check results
    total_classifications = results.qsize()
    total_errors = errors.qsize()

    print(f"Completed {total_classifications} classifications in {elapsed:.2f}s")
    print(f"Errors: {total_errors}")

    if not errors.empty():
        print("Sample errors:", list(errors.queue)[:5])


def test_pattern_compilation_race():
    """Test if pattern compilation has race conditions"""
    print("\n=== Testing Pattern Compilation Race Conditions ===")

    def create_classifier_worker(results_queue):
        try:
            classifier = UFOClassifierService()
            # Check if patterns are compiled
            has_patterns = hasattr(classifier, "compiled_patterns")
            patterns_count = len(classifier.compiled_patterns) if has_patterns else 0
            results_queue.put((has_patterns, patterns_count))
        except Exception as e:
            results_queue.put(("error", str(e)))

    results = queue.Queue()
    threads = []

    # Create many classifiers simultaneously
    for _ in range(30):
        t = threading.Thread(target=create_classifier_worker, args=(results,))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Check results
    all_results = list(results.queue)
    errors = [r for r in all_results if r[0] == "error"]
    successes = [r for r in all_results if r[0] != "error"]

    print(f"Successful initializations: {len(successes)}")
    print(f"Errors: {len(errors)}")

    if successes:
        pattern_counts = [r[1] for r in successes]
        print(f"Pattern counts consistent: {len(set(pattern_counts)) == 1}")


def test_state_corruption():
    """Test if concurrent access can corrupt internal state"""
    print("\n=== Testing State Corruption ===")

    classifier = UFOClassifierService()

    def stress_test_worker(worker_id, iterations, results_queue):
        corrupted = False
        for i in range(iterations):
            try:
                # Perform classification
                result = classifier.classify(
                    f"rechtspersoon_{worker_id}_{i}",
                    "Een juridische entiteit met rechtspersoonlijkheid",
                )

                # Check for corruption indicators
                if result.confidence < 0 or result.confidence > 1:
                    corrupted = True
                    results_queue.put(
                        f"Worker {worker_id}: Invalid confidence {result.confidence}"
                    )

                if result.primary_category is None:
                    corrupted = True
                    results_queue.put(f"Worker {worker_id}: None category")

            except Exception as e:
                results_queue.put(f"Worker {worker_id}: Exception {e}")

        if not corrupted:
            results_queue.put(f"Worker {worker_id}: OK")

    results = queue.Queue()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(stress_test_worker, i, 50, results) for i in range(10)
        ]

        for future in as_completed(futures):
            future.result()

    # Check results
    all_results = list(results.queue)
    ok_count = sum(1 for r in all_results if "OK" in r)
    error_count = len(all_results) - ok_count

    print(f"Workers completed OK: {ok_count}/10")
    if error_count > 0:
        print(f"Errors detected: {error_count}")
        print("Sample errors:", all_results[:5])


def test_global_state_mutation():
    """Test if global state (_classifier_instance) can be corrupted"""
    print("\n=== Testing Global State Mutation ===")

    import src.services.ufo_classifier_service as module

    # Reset global state
    module._classifier_instance = None

    def mutate_global_state(results_queue):
        try:
            # Get instance
            instance1 = get_ufo_classifier()
            id1 = id(instance1)

            # Try to corrupt by direct assignment
            module._classifier_instance = None

            # Get again
            instance2 = get_ufo_classifier()
            id2 = id(instance2)

            results_queue.put((id1, id2, id1 == id2))
        except Exception as e:
            results_queue.put(("error", str(e)))

    results = queue.Queue()
    threads = []

    for _ in range(10):
        t = threading.Thread(target=mutate_global_state, args=(results,))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    all_results = list(results.queue)
    errors = [r for r in all_results if r[0] == "error"]

    print(f"Mutation attempts: {len(all_results)}")
    print(f"Errors: {len(errors)}")

    # Check if IDs are consistent
    id_pairs = [(r[0], r[1]) for r in all_results if r[0] != "error"]
    if id_pairs:
        unique_ids = {id for pair in id_pairs for id in pair}
        print(f"Unique instance IDs created: {len(unique_ids)}")
        print(
            "WARNING: Thread safety issue!"
            if len(unique_ids) > 1
            else "Global state appears thread-safe"
        )


if __name__ == "__main__":
    test_singleton_thread_safety()
    test_concurrent_classification()
    test_pattern_compilation_race()
    test_state_corruption()
    test_global_state_mutation()

    print("\n=== Thread Safety Test Complete ===")
