def get_clock(a):
    if int(a[1]) < 30:
        clock = ["🕐", "🕑", "🕑", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
        clock = clock.pop(int(a[0]) - 1)
    elif int(a[1]) >= 30:
        clock = ["🕜", "🕝", "🕞", "🕟", "🕠", "🕡", "🕢", "🕣", "🕤", "🕥", "🕦", "🕧"]
        clock = clock.pop(int(a[0]) - 1)
    return clock