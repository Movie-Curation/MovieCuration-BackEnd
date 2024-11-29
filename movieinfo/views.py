from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import Follow, ReviewReport
from accounts.serializer import FollowSerializer, ReviewReportSerializer
from accounts.permissions import IsAdminUser  # 관리자 권한 확인

# 팔로잉 리스트 보기
class FollowingListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return Follow.objects.filter(from_user=self.request.user)

# 팔로워 리스트 보기
class FollowersListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return Follow.objects.filter(to_user=self.request.user)

# 관리자 리뷰 신고 관리
class ReviewReportManagementAPIView(APIView):
    """
    관리자 리뷰 신고 관리 API
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """
        신고된 리뷰 목록 조회

        모든 신고된 리뷰의 리스트를 반환합니다. 관리자가 이를 확인하고 조치를 취할 수 있습니다.
        """
        reports = ReviewReport.objects.filter(resolved=False)  # 처리되지 않은 신고
        serializer = ReviewReportSerializer(reports, many=True)
        return Response(serializer.data, status=200)

    def put(self, request, report_id):
        """
        특정 신고를 처리 상태로 업데이트

        신고된 리뷰의 상태(예: 확인 중, 해결 완료)를 변경합니다.
        """
        report = ReviewReport.objects.filter(id=report_id).first()
        if not report:
            return Response({"error": "Report not found."}, status=404)

        report.resolved = True
        report.save()
        return Response({"message": "Report resolved successfully."}, status=200)

# 기본 홈페이지
def index(request):
    return HttpResponse("Welcome to the Movie Info API!")
