public class Fibo {
    public static void main(String[] args) {
        int n = 100;
        int[] fibo = new int[n + 1];
        fibo[0] = 0;
        fibo[1] = 1;
        for (int i = 2; i <= n; i++) {
            fibo[i] = fibo[i - 1] + fibo[i - 2];
        }
        for (int i = 0; i <= n; i++) {
            System.out.print(fibo[i] + " ");
        }
    }
}