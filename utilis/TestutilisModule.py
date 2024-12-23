import unittest

# Function to be tested
def unique(list1):
    # initialize a null list
    unique_list = []
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

class TestUniqueFunction(unittest.TestCase):
    def test_unique_with_duplicates(self):
        # Test case with duplicates
        input_list = [1, 2, 2, 3, 4, 4, 4, 5]
        expected_output = [1, 2, 3, 4, 5]
        self.assertEqual(unique(input_list), expected_output)

    def test_unique_no_duplicates(self):
        # Test case with no duplicates
        input_list = [1, 2, 3, 4, 5]
        expected_output = [1, 2, 3, 4, 5]
        self.assertEqual(unique(input_list), expected_output)

    def test_unique_empty_list(self):
        # Test case with an empty list
        input_list = []
        expected_output = []
        self.assertEqual(unique(input_list), expected_output)

    def test_unique_with_strings(self):
        # Test case with strings
        input_list = ["apple", "banana", "apple", "cherry"]
        expected_output = ["apple", "banana", "cherry"]
        self.assertEqual(unique(input_list), expected_output)

    def test_unique_mixed_types(self):
        # Test case with mixed types
        input_list = [1, "apple", 2, "apple", 1]
        expected_output = [1, "apple", 2]
        self.assertEqual(unique(input_list), expected_output)

if __name__ == "__main__":
    unittest.main()
