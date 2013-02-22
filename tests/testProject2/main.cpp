template<class T>
T function();

template<class T>
T function() {
  return static_cast<T>(function<float>());
}

template<>
int function<int>() {
  return 0;
}

template<>
double function<double>() {
  return 1.0;
}
