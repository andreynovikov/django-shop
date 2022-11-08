import useComparison from '@/lib/comparison';

export default function CompareLink() {
    const { comparisons } = useComparison();

    return (
        <>
            { /*
                <i className="ci-compare text-muted me-2" />Сравнение <span id="compare-notice">{view "sewingworld.views.compare_notice"}</span>
              */
            }
            <i className="ci-compare mt-n1" />
            Сравнение
            { comparisons.length > 0 && (
                <strong> ({ comparisons.length })</strong>
            )}
        </>
    )
}
