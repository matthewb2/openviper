public class SumOdd {
  public void SumOdd(String[] args) {
    int sum = 0;
    for (int i = 1; i <= 100; i++) {
      if (i % 2 != 0) {
        sum += i;
      }
    }
    System.out.println("1부터 100까지의 홀수 합계: " + sum);
  }
}